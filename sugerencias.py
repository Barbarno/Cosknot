"""Sugerencias de título, descripción y etiquetas a partir de la foto.

Es opcional y lo pide el usuario: el botón solo aparece si hay `GEMINI_API_KEY` y
`GEMINI_MODEL`. Sin clave, la función queda desactivada con un motivo y la web
sigue igual.

Se usa el SDK oficial `google-genai` (paquete `google-genai==3.3.0`, import
`from google import genai`). La llamada es `client.models.generate_content(...)`
con una parte de imagen y una parte de texto, y el timeout se pasa en
milisegundos por `types.HttpOptions(timeout=...)`. Una respuesta que no sea JSON
válido se trata como error: no se inventan campos.

La cuota gratuita de Gemini puede usar los datos enviados para mejorar el modelo.
Por eso la web lo dice en el formulario: aquí solo van fotos de demo, y si algún
día se sube material de clientes hay que pasar a una cuenta de pago.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

registro = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 20
TITULO_MAX = 120
DESCRIPCION_MAX = 900
ETIQUETAS_MAX = 6
ETIQUETA_LARGO_MAX = 30

INSTRUCCION = (
    "Eres el asistente de cosknot, un marketplace de cosplay. Miras la foto de una "
    "pieza y propones su ficha en español. Responde solo con un objeto JSON con las "
    "claves titulo (texto corto, máximo 70 caracteres, sin comillas ni prefijos), "
    "descripcion (dos o tres frases sobre materiales, acabado y para qué sirve) y "
    "etiquetas (lista de entre 3 y 6 palabras sueltas en minúsculas). No inventes "
    "marcas ni medidas que no se vean."
)


class SugerenciaError(Exception):
    """Fallo controlado: la ruta lo convierte en un aviso, no en un 500."""

    def __init__(self, mensaje: str, codigo: str = "error") -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


class Sugeridor:
    nombre = "base"
    activo = False
    motivo = ""

    def sugerir(self, imagen: bytes, mime: str, pista: str = "") -> dict[str, Any]:
        raise NotImplementedError


class SugeridorDesactivado(Sugeridor):
    nombre = "desactivado"

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo

    def sugerir(self, imagen: bytes, mime: str, pista: str = "") -> dict[str, Any]:
        raise SugerenciaError(self.motivo or "sugerencias desactivadas", "desactivado")


class SugeridorGemini(Sugeridor):
    nombre = "gemini"
    activo = True

    def __init__(
        self,
        api_key: str,
        modelo: str,
        timeout: int = TIMEOUT_SEGUNDOS,
        cliente: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.modelo = modelo
        self.timeout = timeout
        self._cliente = cliente

    def _construir_cliente(self) -> Any:
        from google import genai
        from google.genai import types

        return genai.Client(
            api_key=self.api_key,
            # El SDK mide el timeout en milisegundos.
            http_options=types.HttpOptions(timeout=self.timeout * 1000),
        )

    def cliente(self) -> Any:
        if self._cliente is None:
            self._cliente = self._construir_cliente()
        return self._cliente

    def _pedir(self, imagen: bytes, mime: str, pista: str) -> str:
        from google.genai import types

        texto = INSTRUCCION
        if pista.strip():
            texto += f"\nPista del vendedor: {pista.strip()[:300]}"

        respuesta = self.cliente().models.generate_content(
            model=self.modelo,
            contents=[
                types.Part.from_bytes(data=imagen, mime_type=mime),
                texto,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
                max_output_tokens=600,
            ),
        )
        return (getattr(respuesta, "text", None) or "").strip()

    def sugerir(self, imagen: bytes, mime: str, pista: str = "") -> dict[str, Any]:
        if not imagen:
            raise SugerenciaError("no hay foto que analizar", "sin_foto")
        try:
            bruto = self._pedir(imagen, mime, pista)
        except Exception as error:  # noqa: BLE001 - se traduce a un aviso para la web
            mensaje = str(error)
            codigo = "cuota" if ("429" in mensaje or "RESOURCE_EXHAUSTED" in mensaje) else "error"
            registro.warning("gemini no respondió: %s", error)
            if codigo == "cuota":
                raise SugerenciaError(
                    "se ha agotado la cuota gratuita de sugerencias, prueba más tarde",
                    "cuota",
                ) from error
            raise SugerenciaError("no se pudo pedir la sugerencia", "error") from error

        datos = _leer_json(bruto)
        titulo = _texto(datos.get("titulo"), TITULO_MAX)
        descripcion = _texto(datos.get("descripcion"), DESCRIPCION_MAX)
        etiquetas = _etiquetas(datos.get("etiquetas"))
        if not titulo or not descripcion:
            raise SugerenciaError("la sugerencia vino incompleta", "incompleta")
        return {"titulo": titulo, "descripcion": descripcion, "etiquetas": etiquetas}


def _leer_json(bruto: str) -> dict[str, Any]:
    """Acepta el JSON pelado o dentro de un bloque de código."""
    texto = bruto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```[a-zA-Z]*\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        raise SugerenciaError("la respuesta no era JSON", "incompleta") from error
    if not isinstance(datos, dict):
        raise SugerenciaError("la respuesta no era un objeto", "incompleta")
    return datos


def _texto(valor: Any, limite: int) -> str:
    if not isinstance(valor, str):
        return ""
    return valor.strip().strip('"').strip()[:limite]


def _etiquetas(valor: Any) -> list[str]:
    if isinstance(valor, str):
        candidatas = re.split(r"[,\n]", valor)
    elif isinstance(valor, list):
        candidatas = [str(elemento) for elemento in valor]
    else:
        return []
    limpias: list[str] = []
    for candidata in candidatas:
        etiqueta = candidata.strip().lower().strip("#.,;")
        if not etiqueta or len(etiqueta) > ETIQUETA_LARGO_MAX:
            continue
        if etiqueta in limpias:
            continue
        limpias.append(etiqueta)
        if len(limpias) >= ETIQUETAS_MAX:
            break
    return limpias


def crear_sugeridor(config: dict[str, Any]) -> Sugeridor:
    clave = (config.get("GEMINI_API_KEY") or "").strip()
    modelo = (config.get("GEMINI_MODEL") or "").strip()
    if not clave:
        return SugeridorDesactivado("falta GEMINI_API_KEY")
    if not modelo:
        return SugeridorDesactivado("falta GEMINI_MODEL")
    try:
        timeout = int((config.get("GEMINI_TIMEOUT") or TIMEOUT_SEGUNDOS))
    except (TypeError, ValueError):
        timeout = TIMEOUT_SEGUNDOS
    return SugeridorGemini(clave, modelo, timeout=max(5, min(timeout, 60)))
