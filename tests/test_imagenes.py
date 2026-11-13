from __future__ import annotations

import pytest
from sqlalchemy import select

from almacenamiento import (
    AlmacenLocal,
    AlmacenR2,
    ErrorImagen,
    crear_almacen,
    validar_imagen,
)
from app import create_app, politica_csp
from models import Work

PNG_MINIMO = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture()
def aplicacion(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'imagenes.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
            "UPLOAD_DIR": (tmp_path / "uploads").as_posix(),
            "IMAGE_STORAGE": "local",
        }
    )


def registrar(cliente, email, rol="creador"):
    return cliente.post(
        "/registro",
        data={
            "email": email,
            "password": "contrasena-larga",
            "confirmar": "contrasena-larga",
            "rol": rol,
        },
        follow_redirects=True,
    )


def taller_con_obra(cliente):
    registrar(cliente, "taller@example.com")
    cliente.post(
        "/cuenta/perfil",
        data={
            "nombre": "Taller Uno",
            "especialidad": "ropa",
            "ubicacion": "Madrid, España",
            "bio": "coso desde 2015.",
            "contacto": "taller@example.com",
        },
    )
    cliente.post(
        "/cuenta/obras/nueva",
        data={
            "titulo": "Capa bordada",
            "descripcion": "capa de lana",
            "precio_nota": "",
            "precio_euros": "120",
            "estado": "disponible",
        },
    )


def test_la_validacion_mira_extension_tipo_tamano_y_firma():
    assert validar_imagen("foto.png", "image/png", PNG_MINIMO, 1024) == ".png"

    with pytest.raises(ErrorImagen):
        validar_imagen("foto.gif", "image/gif", b"GIF89a", 1024)
    with pytest.raises(ErrorImagen):
        validar_imagen("foto.png", "image/jpeg", PNG_MINIMO, 1024)
    with pytest.raises(ErrorImagen):
        validar_imagen("foto.png", "image/png", PNG_MINIMO, 8)
    with pytest.raises(ErrorImagen):
        validar_imagen("foto.png", "image/png", b"no es un png", 1024)
    with pytest.raises(ErrorImagen):
        validar_imagen("foto.png", "image/png", b"", 1024)


def test_sin_claves_de_r2_en_produccion_las_subidas_se_apagan(tmp_path):
    almacen, motivo = crear_almacen(
        {"IMAGE_STORAGE": "local", "UPLOAD_DIR": tmp_path.as_posix()}, produccion=True
    )
    assert almacen is None
    assert "desactivadas" in motivo


def test_si_se_pide_r2_sin_variables_se_avisa_sin_romper(tmp_path):
    almacen, motivo = crear_almacen({"IMAGE_STORAGE": "r2"}, produccion=False)
    assert almacen is None
    assert "R2" in motivo

    almacen, motivo = crear_almacen(
        {
            "IMAGE_STORAGE": "r2",
            "R2_BUCKET": "cosknot",
            "R2_ENDPOINT_URL": "https://cuenta.r2.cloudflarestorage.com",
        },
        produccion=True,
    )
    assert almacen is None
    assert "R2_ACCESS_KEY_ID" in motivo


class ClienteFalso:
    """Sustituye a boto3 en las pruebas: nada sale a la red."""

    def __init__(self):
        self.objetos: dict[str, bytes] = {}
        self.borrados: list[str] = []

    def put_object(self, Bucket, Key, Body, ContentType, CacheControl):
        self.objetos[Key] = Body

    def delete_object(self, Bucket, Key):
        self.borrados.append(Key)


def test_el_almacen_r2_usa_la_api_de_s3_sin_salir_a_la_red():
    falso = ClienteFalso()
    almacen = AlmacenR2(
        bucket="cosknot",
        endpoint_url="https://cuenta.r2.cloudflarestorage.com",
        access_key_id="clave",
        secret_access_key="secreto",
        url_publica="https://img.example.com/",
        cliente=falso,
    )
    almacen.guardar("obras/a.png", PNG_MINIMO, "image/png")
    assert falso.objetos["obras/a.png"] == PNG_MINIMO
    assert almacen.url("obras/a.png") == "https://img.example.com/obras/a.png"
    almacen.borrar("obras/a.png")
    assert falso.borrados == ["obras/a.png"]


def test_el_almacen_local_no_escribe_fuera_de_su_raiz(tmp_path):
    almacen = AlmacenLocal(tmp_path)
    almacen.guardar("obras/a.png", PNG_MINIMO, "image/png")
    assert (tmp_path / "obras" / "a.png").read_bytes() == PNG_MINIMO
    with pytest.raises(ErrorImagen):
        almacen.guardar("../fuera.png", PNG_MINIMO, "image/png")


def test_subir_la_foto_de_una_obra_la_guarda_y_la_enlaza(aplicacion, tmp_path):
    taller = aplicacion.test_client()
    taller_con_obra(taller)

    with aplicacion.extensions["db_session"]() as sesion:
        obra_id = sesion.scalar(select(Work.id).where(Work.slug == "capa-bordada"))

    respuesta = taller.post(
        f"/cuenta/obras/{obra_id}/foto",
        data={"foto": (__import__("io").BytesIO(PNG_MINIMO), "capa.png", "image/png")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "foto de la obra actualizada" in respuesta.get_data(as_text=True)

    with aplicacion.extensions["db_session"]() as sesion:
        obra = sesion.get(Work, obra_id)
        assert obra.image_key is not None
        assert obra.image_key.startswith("obras/")
        clave = obra.image_key

    assert (tmp_path / "uploads" / clave).is_file()


def test_una_foto_invalida_no_toca_la_obra(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)

    with aplicacion.extensions["db_session"]() as sesion:
        obra_id = sesion.scalar(select(Work.id).where(Work.slug == "capa-bordada"))

    respuesta = taller.post(
        f"/cuenta/obras/{obra_id}/foto",
        data={"foto": (__import__("io").BytesIO(b"GIF89a..."), "capa.gif", "image/gif")},
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert "formato no admitido" in respuesta.get_data(as_text=True)

    with aplicacion.extensions["db_session"]() as sesion:
        assert sesion.get(Work, obra_id).image_key is None


def test_otro_creador_no_puede_cambiar_la_foto_ajena(aplicacion):
    taller = aplicacion.test_client()
    taller_con_obra(taller)
    with aplicacion.extensions["db_session"]() as sesion:
        obra_id = sesion.scalar(select(Work.id).where(Work.slug == "capa-bordada"))

    intruso = aplicacion.test_client()
    registrar(intruso, "intruso@example.com")
    respuesta = intruso.post(
        f"/cuenta/obras/{obra_id}/foto",
        data={"foto": (__import__("io").BytesIO(PNG_MINIMO), "x.png", "image/png")},
        content_type="multipart/form-data",
    )
    assert respuesta.status_code == 403


def test_la_csp_solo_abre_img_src_cuando_hay_dominio_de_imagenes(aplicacion):
    sin_r2 = politica_csp(aplicacion)
    assert "img-src" not in sin_r2
    assert "default-src 'self'" in sin_r2

    aplicacion.config["R2_PUBLIC_BASE_URL"] = "https://img.cosknot.example/obras"
    con_r2 = politica_csp(aplicacion)
    assert "img-src 'self' data: https://img.cosknot.example" in con_r2
    assert "*" not in con_r2


def test_la_csp_se_manda_en_la_respuesta(aplicacion):
    respuesta = aplicacion.test_client().get("/")
    assert "Content-Security-Policy" in respuesta.headers
    assert "object-src 'none'" in respuesta.headers["Content-Security-Policy"]
