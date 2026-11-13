"""Envío de correo.

Resend por HTTP, nunca SMTP: Render free bloquea las salidas a 25, 465 y 587.

Hay dos backends con la misma interfaz:

- `CorreoConsola`: escribe el correo en la salida estándar. Es el de desarrollo y
  el de las pruebas, así que nada sale a la red.
- `CorreoResend`: llama a la API de Resend con la clave de `RESEND_API_KEY`.

`crear_correo()` decide cuál toca. Si falta la clave, el correo queda desactivado
con un motivo y la web sigue funcionando: un aviso que no sale no puede tumbar un
pedido.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

registro = logging.getLogger(__name__)

TIMEOUT_SEGUNDOS = 5


class Correo:
    nombre = "base"
    activo = False

    def enviar(self, para: str, asunto: str, texto: str) -> bool:
        raise NotImplementedError


class CorreoConsola(Correo):
    """Desarrollo: el correo se imprime, no se envía."""

    nombre = "consola"
    activo = True

    def enviar(self, para: str, asunto: str, texto: str) -> bool:
        print(f"[correo] para={para} asunto={asunto}")
        for linea in texto.splitlines():
            print(f"[correo]   {linea}")
        return True


class CorreoResend(Correo):
    nombre = "resend"
    activo = True

    def __init__(
        self,
        api_key: str,
        remitente: str,
        responder_a: str | None = None,
        enviar_fn: Any | None = None,
    ) -> None:
        self.api_key = api_key
        self.remitente = remitente
        self.responder_a = responder_a
        self._enviar_fn = enviar_fn

    def _enviar_api(self, para: str, asunto: str, texto: str) -> Any:
        import resend
        from resend.http_client_requests import RequestsClient

        resend.api_key = self.api_key
        # El cliente por defecto espera 30 s; un pedido no puede quedarse colgado
        # de un tercero, así que se baja a 5 s.
        resend.default_http_client = RequestsClient(timeout=TIMEOUT_SEGUNDOS)

        parametros: dict[str, Any] = {
            "from": self.remitente,
            "to": [para],
            "subject": asunto,
            "text": texto,
        }
        if self.responder_a:
            parametros["reply_to"] = self.responder_a
        return resend.Emails.send(parametros)

    def enviar(self, para: str, asunto: str, texto: str) -> bool:
        funcion = self._enviar_fn or self._enviar_api
        try:
            funcion(para, asunto, texto)
        except Exception as error:  # noqa: BLE001 - un fallo de correo no rompe nada
            registro.warning("no se pudo enviar el correo a %s: %s", para, error)
            return False
        return True


class CorreoDesactivado(Correo):
    nombre = "desactivado"
    activo = False

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo

    def enviar(self, para: str, asunto: str, texto: str) -> bool:
        registro.info("correo desactivado (%s): %s", self.motivo, asunto)
        return False


def crear_correo(config: dict[str, Any]) -> Correo:
    clave = (config.get("RESEND_API_KEY") or "").strip()
    remitente = (config.get("EMAIL_FROM") or "").strip()
    responder_a = (config.get("EMAIL_REPLY_TO") or "").strip() or None

    if not clave:
        return CorreoDesactivado("falta RESEND_API_KEY")
    if not remitente:
        return CorreoDesactivado("falta EMAIL_FROM")
    return CorreoResend(clave, remitente, responder_a)


def enviar(correo: Correo, para: str, asunto: str, texto: str, sincrono: bool) -> None:
    """Envía en un hilo aparte para no meter la latencia de Resend en la petición."""
    if not para:
        return
    if sincrono or not correo.activo:
        correo.enviar(para, asunto, texto)
        return
    hilo = threading.Thread(
        target=correo.enviar,
        args=(para, asunto, texto),
        name="correo",
        daemon=True,
    )
    hilo.start()
