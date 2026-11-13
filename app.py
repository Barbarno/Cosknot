"""Aplicación de cosknot: rutas públicas, base de datos y health check."""

from __future__ import annotations

import os
from pathlib import Path
import hashlib
from typing import Any
from xml.sax.saxutils import escape

import click
from flask import Flask, Response, g, render_template, request, url_for
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from werkzeug.middleware.proxy_fix import ProxyFix

from db import DEFAULT_DATABASE_URL, build_engine, normalize_database_url
from almacenamiento import crear_almacen, origen_de
from busqueda import buscar_creadores, buscar_obras
from correo import CorreoConsola, crear_correo
from pagos import motivo_desactivado
from extensiones import csrf, limiter, login_manager
from formularios import PedidoForm
from fotos import foto
from importes import formato_importe
from models import Base, Creator, User, Work
from seed import SPECIALTIES, seed_database


def politica_csp(app: Flask) -> str:
    """CSP base; se abre solo lo que de verdad se usa."""
    partes = [
        "default-src 'self'",
        "object-src 'none'",
        "base-uri 'none'",
        "frame-ancestors 'none'",
    ]
    # Checkout alojado: el POST del pago responde 303 hacia checkout.stripe.com y
    # algunos navegadores aplican form-action también a esa redirección. Es la
    # opción más estrecha: el origen exacto, sin comodín, y solo si el cobro está
    # configurado.
    form_action = ["'self'"]
    if not motivo_desactivado(app.config):
        form_action.append("https://checkout.stripe.com")
    partes.insert(3, "form-action " + " ".join(form_action))

    origen = origen_de(app.config.get("R2_PUBLIC_BASE_URL") or "")
    if origen:
        partes.append(f"img-src 'self' data: {origen}")
    return "; ".join(partes)

# Fotos de piezas y talleres sacadas de Wikimedia Commons (licencias libres).
# La lista es explícita porque cada foto se eligió a mano para que pegue con la
# pieza: un casco no puede llevar la foto de un vestido.
FOTO_OBRA = {
    "abrigo-de-invierno-fantasia": "obra-abrigo-de-invierno-fantasia.jpg",
    "vestido-de-gala-anime": "obra-vestido-de-gala-anime.jpg",
    "espada-de-caballero-de-fantasia": "obra-espada-de-caballero-de-fantasia.jpg",
    "pistola-de-ciencia-ficcion": "cat-props-2.jpg",
    "peluca-estilizada-personaje": "obra-peluca-estilizada-personaje.jpg",
    "extensiones-de-color-a-medida": "obra-extensiones-de-color-a-medida.jpg",
    "casco-de-soldado-espacial": "obra-casco-de-soldado-espacial.jpg",
    "hombreras-de-cuero-sintetico": "obra-hombreras-de-cuero-sintetico.jpg",
    "capa-con-capucha-bordada": "obra-capa-con-capucha-bordada.jpg",
    "armadura-textil-acolchada": "pieza-01.jpg",
    "arnes-de-cuero-con-remaches": "pieza-10.jpg",
    "funda-de-daga-de-fantasia": "pieza-09.jpg",
    "guantes-de-armadura-fantasia": "obra-guantes-de-armadura-fantasia.jpg",
    "garras-de-criatura": "pieza-07.jpg",
    "mascara-de-criatura-del-bosque": "pieza-04.jpg",
}

FOTO_TALLER = {
    "marisol-vega": "taller-marisol-vega.jpg",
    "tomas-iriarte": "pieza-11.jpg",
    "lucia-ferrer": "taller-lucia-ferrer.jpg",
    "iker-zabaleta": "pieza-01.jpg",
    "valentina-ortiz": "taller-valentina-ortiz.jpg",
    "diego-salazar": "pieza-10.jpg",
    "sofia-bianchi": "pieza-04.jpg",
}

FOTOS = sorted(p.name for p in (Path(__file__).parent / "static" / "img").glob("*.jpg"))


def foto_de(slug: str) -> str:
    nombre = FOTO_OBRA.get(slug) or FOTO_TALLER.get(slug)
    if nombre is None and FOTOS:
        indice = int(hashlib.md5(slug.encode("utf-8")).hexdigest(), 16) % len(FOTOS)
        nombre = FOTOS[indice]
    return f"/static/img/{nombre}" if nombre else ""

# El equipo que hay detrás de la web. Los creadores que venden son otra cosa:
# son usuarios verificados, no nosotros.
EQUIPO = [
    {
        "nombre": "Daniel Barrasa",
        "iniciales": "DB",
        "rol": "CEO y CMO",
        "accent": 0,
        "que_hace": (
            "Lleva el rumbo del proyecto: qué se publica, cómo se cuenta y qué se "
            "deja para más adelante. También escribe la documentación."
        ),
        "extra": "Contesta el correo de cosknot y revisa los talleres antes de darles de alta.",
    },
    {
        "nombre": "Jesús Larrazabal",
        "iniciales": "JL",
        "rol": "CTO",
        "accent": 1,
        "que_hace": (
            "Lleva el desarrollo: la web, la base de datos y el despliegue. Es quien "
            "mira los errores del servidor y arregla lo que se rompe."
        ),
        "extra": "Montó la integración con la base de datos y el dominio.",
    },
    {
        "nombre": "Daniel Torres",
        "iniciales": "DT",
        "rol": "CFO",
        "accent": 2,
        "que_hace": (
            "Lleva las cuentas: lo que cuesta mantener la web y lo que habría que "
            "cobrar de comisión cuando lleguen las ventas."
        ),
        "extra": "Controla el gasto de los servicios y los plazos.",
    },
]


def debe_sembrar(url: str, seed_on_start: str | None) -> bool:
    """El catálogo de ejemplo se siembra en local (SQLite) o si se pide a mano."""
    return url.startswith("sqlite") or seed_on_start == "1"


def es_produccion() -> bool:
    """¿Estamos sirviendo la web de verdad?

    Heroku no deja una variable de entorno propia y fiable salvo `DYNO`, así que
    el criterio es explícito: `APP_ENV=production` manda; si no está puesta, la
    presencia de `DYNO` (un dyno de Heroku) implica producción. En local no hay
    ninguna de las dos y la app arranca en modo desarrollo.
    """
    entorno = (
        os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or ""
    ).strip().lower()
    if entorno:
        return entorno in ("production", "prod")
    return bool(os.environ.get("DYNO"))


def proxies_de_confianza() -> tuple[int, int]:
    """Número de proxies de confianza para X-Forwarded-For y X-Forwarded-Proto.

    La cadena real es Cloudflare (solo DNS, ver docs/decisions/0003) → router de
    Heroku → gunicorn → app. Con Cloudflare en modo "DNS only" el único proxy que
    añade cabeceras es el router de Heroku, así que se confía en un solo salto.
    Si algún día se activa el proxy naranja de Cloudflare, hay que subir
    `PROXY_FIX_X_FOR` a 2 o el límite de intentos contará la IP del edge.

    Se acota a 0..5 para que un valor absurdo en una config var no permita
    falsificar la IP desde el cliente.
    """

    def leer(variable: str) -> int:
        crudo = (os.environ.get(variable) or "1").strip()
        try:
            valor = int(crudo)
        except ValueError:
            return 1
        return max(0, min(5, valor))

    return leer("PROXY_FIX_X_FOR"), leer("PROXY_FIX_X_PROTO")


def configurar_registro(nivel: str | None = None) -> None:
    """Nivel de log por variable de entorno; por defecto INFO."""
    import logging

    nombre = (nivel or os.environ.get("LOG_LEVEL") or "INFO").strip().upper()
    valor = getattr(logging, nombre, None)
    if not isinstance(valor, int):
        valor = logging.INFO
    logging.basicConfig(
        level=valor,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger().setLevel(valor)


def configurar_sentry(app: Flask) -> bool:
    """Sentry solo si hay SENTRY_DSN. Sin DSN no se inicializa nada."""
    dsn = (os.environ.get("SENTRY_DSN") or "").strip()
    if not dsn or app.config.get("TESTING"):
        return False
    if app.extensions.get("sentry_iniciado"):
        return True

    import sentry_sdk

    muestra = os.environ.get("SENTRY_TRACES_SAMPLE_RATE") or "0"
    try:
        tasa = float(muestra)
    except ValueError:
        tasa = 0.0

    sentry_sdk.init(
        dsn=dsn,
        environment=os.environ.get("SENTRY_ENVIRONMENT") or "production",
        traces_sample_rate=tasa,
        send_default_pii=False,
    )
    app.extensions["sentry_iniciado"] = True
    return True


def create_app(config: dict[str, Any] | None = None) -> Flask:
    configurar_registro()
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URL=normalize_database_url(os.environ.get("DATABASE_URL")),
        SECRET_KEY=os.environ.get("SECRET_KEY"),
    )
    if config:
        app.config.update(config)
        app.config["DATABASE_URL"] = normalize_database_url(app.config["DATABASE_URL"])

    es_test = bool(app.config.get("TESTING"))
    produccion = es_produccion() and not es_test

    # En producción, si falta una variable el arranque tiene que romper. Con los
    # valores por defecto que había antes, la app respondía 200 firmada con un
    # secreto publicado en el repo, o con la base de datos en el disco efímero del
    # contenedor, y los datos desaparecían en el siguiente despliegue.
    if produccion:
        faltan = [k for k in ("SECRET_KEY", "DATABASE_URL") if not os.environ.get(k)]
        if faltan:
            raise RuntimeError(
                "faltan variables de entorno en producción: " + ", ".join(faltan)
            )

    # El router de Heroku termina el TLS y reenvía X-Forwarded-Proto y
    # X-Forwarded-For. Sin ProxyFix, Flask creería que la petición va por http
    # (redirecciones a sí misma en bucle) y `request.remote_addr` sería el del
    # router, con lo que el límite de intentos contaría a todos los visitantes en
    # el mismo cubo. Se confía solo en los saltos declarados.
    x_for, x_proto = proxies_de_confianza()
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=x_for, x_proto=x_proto, x_host=0, x_port=0
    )

    engine = build_engine(app.config["DATABASE_URL"])
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = session_factory

    es_sqlite = app.config["DATABASE_URL"].startswith("sqlite")

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        # Secure solo cuando la web va por https: en local (http) el navegador no
        # enviaría la cookie y no se podría entrar.
        SESSION_COOKIE_SECURE=produccion,
    )
    # El almacenamiento del límite de intentos. En Heroku no hay Redis (3 $ más
    # romperían el tope de 13), así que va en memoria del único proceso web: es
    # exacto mientras haya un worker, y se pierde al reiniciar el dyno.
    app.config.setdefault(
        "RATELIMIT_STORAGE_URI",
        (os.environ.get("RATELIMIT_STORAGE_URI") or "memory://").strip(),
    )
    # En tests se desactivan por defecto; una prueba puede volver a activarlos
    # pasándolos en `config`.
    app.config.setdefault("WTF_CSRF_ENABLED", not es_test)
    app.config.setdefault("RATELIMIT_ENABLED", not es_test)

    # Almacenamiento de imágenes. Sin R2 en producción la subida queda apagada y
    # la web lo dice; nunca revienta el arranque.
    app.config.setdefault("UPLOAD_DIR", os.environ.get("UPLOAD_DIR") or "static/uploads")
    app.config.setdefault("IMAGE_STORAGE", os.environ.get("IMAGE_STORAGE") or "")
    for variable in (
        "R2_BUCKET",
        "R2_ENDPOINT_URL",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_PUBLIC_BASE_URL",
    ):
        app.config.setdefault(variable, os.environ.get(variable))
    # Tope global de subida: una petición mayor se corta antes de leer el cuerpo.
    app.config.setdefault("MAX_CONTENT_LENGTH", 8 * 1024 * 1024)
    app.config.setdefault("MAX_IMAGE_BYTES", 5 * 1024 * 1024)

    almacen, motivo_almacen = crear_almacen(app.config, produccion=produccion)
    app.extensions["almacen"] = almacen
    app.extensions["almacen_motivo"] = motivo_almacen

    # Correo. Sin RESEND_API_KEY o sin EMAIL_FROM se usa la consola en desarrollo y
    # queda desactivado en producción, sin tumbar el arranque.
    app.config.setdefault("RESEND_API_KEY", os.environ.get("RESEND_API_KEY"))
    app.config.setdefault("EMAIL_FROM", os.environ.get("EMAIL_FROM"))
    app.config.setdefault("EMAIL_REPLY_TO", os.environ.get("EMAIL_REPLY_TO"))
    # EMAIL_ASYNC=1 (defecto): si el envío en la petición falla, el aviso va a
    # email_outbox y el hilo lo reintenta. 0: se intenta una vez y se descarta.
    app.config.setdefault(
        "EMAIL_ASYNC", (os.environ.get("EMAIL_ASYNC") or "1") != "0" and not es_test
    )
    app.config.setdefault(
        "EMAIL_MAX_INTENTOS", os.environ.get("EMAIL_MAX_INTENTOS") or "5"
    )
    configurar_sentry(app)
    correo = crear_correo(app.config)
    if correo.nombre == "desactivado" and not produccion:
        correo = CorreoConsola()
    app.extensions["correo"] = correo

    # Stripe Connect. Sin claves de prueba, sin webhook o sin COMMISSION_PERCENT el
    # cobro queda desactivado: no se inventa un porcentaje.
    for variable in (
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "COMMISSION_PERCENT",
    ):
        app.config.setdefault(variable, os.environ.get(variable))

    # En SQLite (local y tests) el esquema se crea con create_all: es instantáneo
    # e idempotente. En PostgreSQL lo mueve Alembic desde el proceso `release`
    # del Procfile, una sola vez por despliegue; si la migración falla, Heroku
    # aborta el despliegue y sigue sirviendo la versión anterior.
    if es_sqlite:
        Base.metadata.create_all(engine)

    # El catálogo de ejemplo solo se siembra en local o cuando se pide a mano con
    # SEED_ON_START=1 / `flask sembrar`. En producción no se toca la base al arrancar.
    if debe_sembrar(app.config["DATABASE_URL"], os.environ.get("SEED_ON_START")):
        # Cada proceso que arranca puede ver las tablas vacías y sembrar a la vez;
        # el segundo choca contra el índice único de slug. Perder esa carrera es
        # lo normal y no es un error.
        try:
            with session_factory() as bootstrap:
                seed_database(bootstrap)
        except IntegrityError:
            pass

    @app.cli.command("sembrar")
    def sembrar_comando() -> None:
        """Siembra el catálogo de ejemplo en la base configurada."""
        with session_factory() as sesion:
            seed_database(sesion)
        print("catálogo sembrado")

    @app.cli.command("migrar-fotos")
    def migrar_fotos() -> None:
        """Sube las fotos de static/img al almacén y las enlaza a cada ficha."""
        from fotos import DIRECTORIO_IMAGENES, nombre_actual

        almacen = app.extensions.get("almacen")
        if almacen is None:
            raise click.ClickException(
                "no hay almacén configurado: " + (app.extensions.get("almacen_motivo") or "")
            )

        subidas = 0
        with session_factory() as sesion:
            for entidad in (
                *sesion.scalars(select(Creator)).all(),
                *sesion.scalars(select(Work)).all(),
            ):
                if entidad.image_key:
                    continue
                nombre = nombre_actual(entidad.slug)
                if not nombre:
                    continue
                ruta = DIRECTORIO_IMAGENES / nombre
                if not ruta.is_file():
                    continue
                clave = f"obras/{nombre}"
                almacen.guardar(clave, ruta.read_bytes(), "image/jpeg")
                entidad.image_key = clave
                subidas += 1
            sesion.commit()
        print(f"fotos migradas: {subidas}")

    @app.cli.command("hacer-admin")
    @click.argument("email")
    def hacer_admin(email: str) -> None:
        """Marca como admin la cuenta con ese correo (debe existir ya)."""
        from seguridad import normalizar_email

        with session_factory() as sesion:
            usuario = sesion.scalar(
                select(User).where(User.email == normalizar_email(email))
            )
            if usuario is None:
                raise click.ClickException(f"no hay ninguna cuenta con {email}")
            usuario.role = "admin"
            sesion.commit()
        print(f"{email} es admin")

    @app.before_request
    def open_session() -> None:
        g.db = session_factory()

    @app.teardown_request
    def close_session(exception: BaseException | None) -> None:
        session: Session | None = g.pop("db", None)
        if session is not None:
            session.close()

    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def cargar_usuario(user_id: str) -> User | None:
        sesion: Session | None = getattr(g, "db", None)
        if sesion is None:
            return None
        try:
            return sesion.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    from admin import bp as admin_bp
    from auth import bp as auth_bp
    from cobros import bp as cobros_bp
    from cuenta import bp as cuenta_bp
    from pedidos import bp as pedidos_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cuenta_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(cobros_bp)

    @app.after_request
    def cabeceras_de_seguridad(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), camera=(), microphone=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy", politica_csp(app),
        )
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        # El alias de Heroku sirve la misma app y no quiero que compita en
        # buscadores con el dominio propio.
        if request.host.endswith(".herokuapp.com"):
            response.headers.setdefault("X-Robots-Tag", "noindex")
        return response

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        return {
            "specialties": SPECIALTIES,
            "current_year": 2026,
            "equipo": EQUIPO,
            "foto": foto,
            "formato_importe": formato_importe,
            "almacen_activo": app.extensions.get("almacen") is not None,
            "almacen_motivo": app.extensions.get("almacen_motivo") or "",
            "cobro_motivo": motivo_desactivado(app.config),
            "cobro_activo": not motivo_desactivado(app.config),
        }

    @app.route("/")
    def index() -> str:
        featured = g.db.scalars(
            select(Creator).order_by(Creator.id).limit(3)
        ).all()
        works = g.db.scalars(select(Work).order_by(Work.id.desc()).limit(8)).all()
        creator_count = g.db.scalar(select(func.count()).select_from(Creator)) or 0
        return render_template(
            "index.html",
            featured=featured,
            works=works,
            creator_count=creator_count,
        )

    @app.route("/creadores")
    def creators() -> str:
        selected = request.args.get("especialidad", "todas")
        if selected not in SPECIALTIES:
            selected = "todas"
        rows = g.db.scalars(select(Creator).order_by(Creator.name)).all()
        return render_template("creators.html", creators=rows, selected=selected)

    @app.route("/nosotros")
    def nosotros() -> str:
        return render_template("nosotros.html")

    @app.route("/buscar")
    def buscar() -> str:
        consulta = (request.args.get("q") or "").strip()
        creadores: list[Creator] = []
        obras: list[Work] = []
        if consulta:
            creadores = buscar_creadores(g.db, consulta)
            obras = buscar_obras(g.db, consulta)
        return render_template(
            "buscar.html", consulta=consulta, creadores=creadores, obras=obras
        )

    @app.route("/creadores/<slug>")
    def creator_detail(slug: str) -> str:
        creator = g.db.scalar(select(Creator).where(Creator.slug == slug))
        if creator is None:
            return render_template("404.html"), 404
        return render_template("creator.html", creator=creator, works=creator.works)

    @app.route("/obras/<slug>")
    def work_detail(slug: str) -> str:
        work = g.db.scalar(select(Work).where(Work.slug == slug))
        if work is None:
            return render_template("404.html"), 404
        otras = [obra for obra in work.creator.works if obra.id != work.id]
        return render_template(
            "work.html",
            work=work,
            creator=work.creator,
            otras=otras,
            pedido_form=PedidoForm(),
        )

    @app.route("/robots.txt")
    def robots() -> Response:
        sitemap = url_for("sitemap", _external=True)
        body = f"User-agent: *\nAllow: /\nSitemap: {sitemap}\n"
        return Response(body, mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap() -> Response:
        urls = [url_for("index"), url_for("creators"), url_for("nosotros")]
        urls += [url_for("creator_detail", slug=s.slug) for s in g.db.scalars(select(Creator)).all()]
        urls += [url_for("work_detail", slug=w.slug) for w in g.db.scalars(select(Work)).all()]
        entries = "".join(
            f"<url><loc>{escape(request.url_root.rstrip('/'))}{path}</loc></url>"
            for path in urls
        )
        body = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            f"{entries}</urlset>"
        )
        return Response(body, mimetype="application/xml")

    @app.route("/healthz")
    def healthz() -> tuple[dict[str, str], int]:
        try:
            g.db.execute(text("SELECT 1"))
        except Exception:
            return {"status": "error"}, 503
        return {"status": "ok"}, 200

    @app.errorhandler(404)
    def not_found(error: Exception) -> tuple[str, int]:
        return render_template("404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(error: Exception) -> tuple[str, int]:
        # Sin esto, werkzeug devuelve su plantilla en inglés y se nota que es Flask.
        return render_template("404.html"), 405

    return app


app = create_app()
