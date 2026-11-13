from __future__ import annotations

import pytest
from sqlalchemy import select

from app import create_app
from extensiones import limiter
from models import Creator, User, Work


@pytest.fixture()
def aplicacion(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'cuentas.db').as_posix()}",
            "SECRET_KEY": "clave-de-pruebas",
        }
    )


@pytest.fixture()
def cliente(aplicacion):
    return aplicacion.test_client()


def registrar(cliente, email="ana@example.com", password="contrasena-larga", rol="comprador"):
    return cliente.post(
        "/registro",
        data={
            "email": email,
            "password": password,
            "confirmar": password,
            "rol": rol,
        },
        follow_redirects=True,
    )


def crear_perfil(cliente, nombre="Taller Ana"):
    return cliente.post(
        "/cuenta/perfil",
        data={
            "nombre": nombre,
            "especialidad": "ropa",
            "ubicacion": "Madrid, España",
            "bio": "coso desde 2015 y hago patrones propios.",
            "contacto": "ana@example.com",
        },
        follow_redirects=True,
    )


def test_el_registro_crea_la_cuenta_y_abre_sesion(cliente, aplicacion):
    respuesta = registrar(cliente, rol="creador")
    assert respuesta.status_code == 200
    assert "cuenta creada" in respuesta.get_data(as_text=True)

    with aplicacion.extensions["db_session"]() as sesion:
        usuario = sesion.scalar(select(User).where(User.email == "ana@example.com"))
        assert usuario is not None
        assert usuario.role == "creador"
        assert usuario.password_hash.startswith("$argon2")


def test_no_se_puede_registrar_dos_veces_el_mismo_correo(cliente):
    registrar(cliente)
    cliente.post("/salir")
    respuesta = registrar(cliente)
    assert respuesta.status_code == 400
    assert "ya hay una cuenta con ese correo" in respuesta.get_data(as_text=True)


def test_el_registro_rechaza_contrasenas_cortas(cliente):
    respuesta = cliente.post(
        "/registro",
        data={"email": "corta@example.com", "password": "corta", "confirmar": "corta"},
    )
    assert respuesta.status_code == 200
    assert "crear cuenta" in respuesta.get_data(as_text=True)


def test_entrar_con_la_contrasena_mal_da_401(cliente):
    registrar(cliente)
    cliente.post("/salir")
    respuesta = cliente.post(
        "/entrar", data={"email": "ana@example.com", "password": "otra-cosa"}
    )
    assert respuesta.status_code == 401
    assert "incorrectos" in respuesta.get_data(as_text=True)


def test_entrar_y_salir(cliente):
    registrar(cliente)
    cliente.post("/salir")
    respuesta = cliente.post(
        "/entrar",
        data={"email": "ana@example.com", "password": "contrasena-larga"},
        follow_redirects=True,
    )
    assert respuesta.status_code == 200
    assert "mi cuenta" in respuesta.get_data(as_text=True)
    assert "ana@example.com" in respuesta.get_data(as_text=True)

    respuesta = cliente.post("/salir", follow_redirects=True)
    assert "sesión cerrada" in respuesta.get_data(as_text=True)


def test_el_panel_exige_sesion(cliente):
    respuesta = cliente.get("/cuenta/", follow_redirects=False)
    assert respuesta.status_code == 302
    assert "/entrar" in respuesta.headers["Location"]


def test_un_creador_publica_edita_y_borra_sus_obras(cliente, aplicacion):
    registrar(cliente, rol="creador")
    assert "perfil guardado" in crear_perfil(cliente).get_data(as_text=True)

    respuesta = cliente.post(
        "/cuenta/obras/nueva",
        data={
            "titulo": "Capa bordada",
            "descripcion": "capa de lana con bordado a mano",
            "precio_nota": "desde 200 €",
            "estado": "disponible",
        },
        follow_redirects=True,
    )
    assert "obra publicada" in respuesta.get_data(as_text=True)

    with aplicacion.extensions["db_session"]() as sesion:
        obra = sesion.scalar(select(Work).where(Work.title == "Capa bordada"))
        assert obra is not None
        assert obra.slug == "capa-bordada"
        assert obra.creator.user_id is not None
        obra_id = obra.id

    respuesta = cliente.post(
        f"/cuenta/obras/{obra_id}/editar",
        data={
            "titulo": "Capa bordada",
            "descripcion": "capa de lana con bordado a mano y forro",
            "precio_nota": "desde 240 €",
            "estado": "encargo",
        },
        follow_redirects=True,
    )
    assert "obra actualizada" in respuesta.get_data(as_text=True)

    with aplicacion.extensions["db_session"]() as sesion:
        obra = sesion.get(Work, obra_id)
        assert obra.status == "encargo"
        assert obra.price_note == "desde 240 €"

    respuesta = cliente.post(f"/cuenta/obras/{obra_id}/borrar", follow_redirects=True)
    assert "obra borrada" in respuesta.get_data(as_text=True)

    with aplicacion.extensions["db_session"]() as sesion:
        assert sesion.get(Work, obra_id) is None


def test_un_comprador_no_puede_crear_perfil_de_taller(cliente):
    registrar(cliente, rol="comprador")
    respuesta = cliente.get("/cuenta/perfil", follow_redirects=True)
    assert "tu cuenta es de comprador" in respuesta.get_data(as_text=True)


def test_nadie_toca_obras_de_otro_creador(aplicacion):
    otro = aplicacion.test_client()
    registrar(otro, email="otro@example.com", rol="creador")
    crear_perfil(otro, nombre="Taller Otro")
    otro.post(
        "/cuenta/obras/nueva",
        data={
            "titulo": "Casco",
            "descripcion": "casco de resina",
            "precio_nota": "",
            "estado": "disponible",
        },
    )

    with aplicacion.extensions["db_session"]() as sesion:
        obra = sesion.scalar(select(Work).where(Work.title == "Casco"))
        obra_id = obra.id

    intruso = aplicacion.test_client()
    registrar(intruso, email="intruso@example.com", rol="creador")
    crear_perfil(intruso, nombre="Taller Intruso")

    assert intruso.get(f"/cuenta/obras/{obra_id}/editar").status_code == 403
    assert intruso.post(f"/cuenta/obras/{obra_id}/borrar").status_code == 403


def test_el_admin_verifica_y_desverifica_creadores(aplicacion):
    creador = aplicacion.test_client()
    registrar(creador, email="taller@example.com", rol="creador")
    crear_perfil(creador)

    with aplicacion.extensions["db_session"]() as sesion:
        perfil = sesion.scalar(select(Creator).where(Creator.name == "Taller Ana"))
        creador_id = perfil.id

    admin = aplicacion.test_client()
    registrar(admin, email="jefa@example.com")
    with aplicacion.extensions["db_session"]() as sesion:
        usuario = sesion.scalar(select(User).where(User.email == "jefa@example.com"))
        usuario.role = "admin"
        sesion.commit()

    respuesta = admin.get("/admin/creadores")
    assert respuesta.status_code == 200
    assert "Taller Ana" in respuesta.get_data(as_text=True)

    admin.post(f"/admin/creadores/{creador_id}/verificar", follow_redirects=True)
    with aplicacion.extensions["db_session"]() as sesion:
        assert sesion.get(Creator, creador_id).verified is True

    admin.post(f"/admin/creadores/{creador_id}/verificar", follow_redirects=True)
    with aplicacion.extensions["db_session"]() as sesion:
        assert sesion.get(Creator, creador_id).verified is False


def test_un_usuario_normal_no_entra_en_administracion(aplicacion):
    cliente = aplicacion.test_client()
    registrar(cliente)
    assert cliente.get("/admin/creadores").status_code == 403


def test_las_cookies_de_sesion_son_httponly_y_lax(aplicacion):
    assert aplicacion.config["SESSION_COOKIE_HTTPONLY"] is True
    assert aplicacion.config["SESSION_COOKIE_SAMESITE"] == "Lax"


def test_en_produccion_la_cookie_va_marcada_secure(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "clave")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{(tmp_path / 'prod.db').as_posix()}")
    app = create_app({"DATABASE_URL": f"sqlite:///{(tmp_path / 'prod.db').as_posix()}"})
    assert app.config["SESSION_COOKIE_SECURE"] is True
    assert app.config["WTF_CSRF_ENABLED"] is True


def test_el_csrf_bloquea_un_post_sin_token(tmp_path):
    app = create_app(
        {
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'csrf.db').as_posix()}",
            "SECRET_KEY": "clave",
        }
    )
    cliente = app.test_client()
    respuesta = cliente.post(
        "/registro", data={"email": "x@example.com", "password": "contrasena-larga"}
    )
    assert respuesta.status_code == 400


def test_el_login_limita_los_intentos(tmp_path):
    app = create_app(
        {
            "DATABASE_URL": f"sqlite:///{(tmp_path / 'limite.db').as_posix()}",
            "SECRET_KEY": "clave",
            "WTF_CSRF_ENABLED": False,
            "RATELIMIT_ENABLED": True,
        }
    )
    limiter.reset()
    try:
        cliente = app.test_client()
        codigos = [
            cliente.post(
                "/entrar", data={"email": "nadie@example.com", "password": "x" * 12}
            ).status_code
            for _ in range(7)
        ]
    finally:
        limiter.reset()
    assert 429 in codigos
