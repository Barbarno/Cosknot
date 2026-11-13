"""Sugerencias de ficha con Gemini: cliente falso, sin red."""

from __future__ import annotations

import json

import pytest

from app import create_app
from sugerencias import (
    SugerenciaError,
    SugeridorDesactivado,
    SugeridorGemini,
    crear_sugeridor,
)

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c6360000002000100ffff03000006000557bfabd400"
    "00000049454e44ae426082"
)


class RespuestaFalsa:
    def __init__(self, texto: str) -> None:
        self.text = texto


class ModelosFalsos:
    def __init__(self, respuesta: str | Exception) -> None:
        self.respuesta = respuesta
        self.llamadas: list[dict] = []

    def generate_content(self, **kwargs):
        self.llamadas.append(kwargs)
        if isinstance(self.respuesta, Exception):
            raise self.respuesta
        return RespuestaFalsa(self.respuesta)


class ClienteFalso:
    def __init__(self, respuesta: str | Exception) -> None:
        self.models = ModelosFalsos(respuesta)


def test_sin_clave_queda_desactivado():
    sugeridor = crear_sugeridor({})
    assert isinstance(sugeridor, SugeridorDesactivado)
    assert "GEMINI_API_KEY" in sugeridor.motivo
    assert sugeridor.activo is False


def test_con_clave_pero_sin_modelo_no_se_inventa_un_modelo():
    sugeridor = crear_sugeridor({"GEMINI_API_KEY": "clave"})
    assert isinstance(sugeridor, SugeridorDesactivado)
    assert "GEMINI_MODEL" in sugeridor.motivo


def test_con_clave_y_modelo_se_activa():
    sugeridor = crear_sugeridor(
        {"GEMINI_API_KEY": "clave", "GEMINI_MODEL": "gemini-2.5-flash"}
    )
    assert isinstance(sugeridor, SugeridorGemini)
    assert sugeridor.modelo == "gemini-2.5-flash"
    assert sugeridor.timeout == 20


def test_el_timeout_se_acota():
    sugeridor = crear_sugeridor(
        {"GEMINI_API_KEY": "k", "GEMINI_MODEL": "m", "GEMINI_TIMEOUT": "900"}
    )
    assert sugeridor.timeout == 60
    sugeridor = crear_sugeridor(
        {"GEMINI_API_KEY": "k", "GEMINI_MODEL": "m", "GEMINI_TIMEOUT": "1"}
    )
    assert sugeridor.timeout == 5


def test_la_sugerencia_se_limpia_y_se_acota():
    cuerpo = json.dumps(
        {
            "titulo": "  Capa bordada de lana  ",
            "descripcion": "  Capa de lana con bordado a mano.  ",
            "etiquetas": ["Capa", "lana", "capa", "", "#medieval", "invierno", "extra"],
        }
    )
    cliente = ClienteFalso(cuerpo)
    sugeridor = SugeridorGemini("clave", "gemini-2.5-flash", cliente=cliente)

    resultado = sugeridor.sugerir(PNG, "image/png", "capa de invierno")

    assert resultado["titulo"] == "Capa bordada de lana"
    assert resultado["descripcion"] == "Capa de lana con bordado a mano."
    assert resultado["etiquetas"] == ["capa", "lana", "medieval", "invierno", "extra"]

    llamada = cliente.models.llamadas[0]
    assert llamada["model"] == "gemini-2.5-flash"
    assert llamada["config"].response_mime_type == "application/json"
    # la foto va como parte binaria con su tipo
    partes = llamada["contents"]
    assert partes[0].inline_data.mime_type == "image/png"
    assert "capa de invierno" in partes[1]


def test_acepta_json_dentro_de_un_bloque_de_codigo():
    cuerpo = "```json\n" + json.dumps(
        {"titulo": "Peluca", "descripcion": "Peluca larga.", "etiquetas": ["peluca"]}
    ) + "\n```"
    sugeridor = SugeridorGemini("k", "m", cliente=ClienteFalso(cuerpo))
    resultado = sugerir_con(sugeridor)
    assert resultado["titulo"] == "Peluca"


def sugerir_con(sugeridor):
    return sugeridor.sugerir(PNG, "image/png")


def test_una_respuesta_incompleta_es_error():
    sugeridor = SugeridorGemini("k", "m", cliente=ClienteFalso('{"titulo": "solo"}'))
    with pytest.raises(SugerenciaError) as error:
        sugerir_con(sugeridor)
    assert error.value.codigo == "incompleta"


def test_una_respuesta_que_no_es_json_es_error():
    sugeridor = SugeridorGemini("k", "m", cliente=ClienteFalso("no soy json"))
    with pytest.raises(SugerenciaError):
        sugerir_con(sugeridor)


def test_la_cuota_agotada_se_explica():
    sugeridor = SugeridorGemini(
        "k", "m", cliente=ClienteFalso(RuntimeError("429 RESOURCE_EXHAUSTED"))
    )
    with pytest.raises(SugerenciaError) as error:
        sugerir_con(sugeridor)
    assert error.value.codigo == "cuota"
    assert "cuota" in error.value.mensaje


def test_sin_foto_no_se_llama_al_modelo():
    sugeridor = SugeridorGemini("k", "m", cliente=ClienteFalso("{}"))
    with pytest.raises(SugerenciaError):
        sugeridor.sugerir(b"", "image/png")


@pytest.fixture()
def aplicacion(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'sug.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
        }
    )


def _entrar_como_creador(cliente):
    cliente.post(
        "/registro",
        data={
            "email": "sugerencias@example.com",
            "password": "contrasena-larga",
            "confirmar": "contrasena-larga",
            "rol": "creador",
        },
    )
    cliente.post(
        "/cuenta/perfil",
        data={
            "nombre": "Taller Sugerencias",
            "especialidad": "ropa",
            "ubicacion": "Madrid, España",
            "bio": "coso desde 2015.",
            "contacto": "hola@taller.example",
        },
    )


def test_sin_clave_el_boton_no_aparece(aplicacion):
    cliente = aplicacion.test_client()
    _entrar_como_creador(cliente)
    cuerpo = cliente.get("/cuenta/obras/nueva").get_data(as_text=True)
    assert "data-sugerencias" not in cuerpo
    assert "sugerencias.js" not in cuerpo


def test_sin_clave_la_ruta_responde_404(aplicacion):
    cliente = aplicacion.test_client()
    _entrar_como_creador(cliente)
    respuesta = cliente.post("/cuenta/obras/sugerencias")
    assert respuesta.status_code == 404


def test_con_clave_el_boton_aparece_y_la_ruta_devuelve_la_ficha(tmp_path):
    aplicacion = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'sug2.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
            "GEMINI_API_KEY": "clave",
            "GEMINI_MODEL": "gemini-2.5-flash",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )
    cliente_falso = ClienteFalso(
        json.dumps(
            {
                "titulo": "Capa bordada",
                "descripcion": "Capa de lana con bordado a mano.",
                "etiquetas": ["capa", "lana"],
            }
        )
    )
    aplicacion.extensions["sugeridor"] = SugeridorGemini(
        "clave", "gemini-2.5-flash", cliente=cliente_falso
    )

    cliente = aplicacion.test_client()
    _entrar_como_creador(cliente)

    cuerpo = cliente.get("/cuenta/obras/nueva").get_data(as_text=True)
    assert "data-sugerencias" in cuerpo
    assert "sugerencias.js" in cuerpo

    respuesta = cliente.post(
        "/cuenta/obras/sugerencias",
        data={"foto": (open_png(), "capa.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert respuesta.status_code == 200
    datos = respuesta.get_json()
    assert datos["sugerencia"]["titulo"] == "Capa bordada"
    assert datos["sugerencia"]["etiquetas"] == ["capa", "lana"]


def test_una_foto_que_no_es_imagen_se_rechaza(tmp_path):
    aplicacion = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'sug3.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
            "GEMINI_API_KEY": "clave",
            "GEMINI_MODEL": "gemini-2.5-flash",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": False,
        }
    )
    aplicacion.extensions["sugeridor"] = SugeridorGemini(
        "clave", "gemini-2.5-flash", cliente=ClienteFalso("{}")
    )
    cliente = aplicacion.test_client()
    _entrar_como_creador(cliente)

    respuesta = cliente.post(
        "/cuenta/obras/sugerencias",
        data={"foto": (open_texto(), "notas.txt", "text/plain")},
        content_type="multipart/form-data",
    )
    assert respuesta.status_code == 400
    assert "error" in respuesta.get_json()


def open_png():
    import io

    return io.BytesIO(PNG)


def open_texto():
    import io

    return io.BytesIO(b"no soy una imagen")
