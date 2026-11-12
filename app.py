"""Aplicación de cosknot: rutas públicas, base de datos y health check."""

from __future__ import annotations

import os
from typing import Any
from xml.sax.saxutils import escape

from flask import Flask, Response, g, render_template, request, url_for
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base, Creator, Work
from seed import SPECIALTIES, seed_database

DEFAULT_DATABASE_URL = "sqlite:///cosknot.db"


def normalize_database_url(url: str | None) -> str:
    if not url:
        return DEFAULT_DATABASE_URL
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def build_engine(url: str) -> Engine:
    options: dict[str, Any] = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if ":memory:" in url or url.endswith(":memory:"):
            options["poolclass"] = StaticPool
    else:
        options["pool_pre_ping"] = True
        # Neon va por pgbouncer en modo transacción: no guarda estado entre
        # transacciones, así que los prepared statements que cachea psycopg3
        # fallan. Desactivando la caché no hay problema.
        options["connect_args"] = {"sslmode": "require", "prepare_threshold": None}
    return create_engine(url, **options)


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URL=normalize_database_url(os.environ.get("DATABASE_URL")),
        SECRET_KEY=os.environ.get("SECRET_KEY"),
    )
    if config:
        app.config.update(config)
        app.config["DATABASE_URL"] = normalize_database_url(app.config["DATABASE_URL"])

    # En producción, si falta una variable el arranque tiene que romper. Con los
    # valores por defecto que había antes, la app respondía 200 firmada con un
    # secreto publicado en el repo, o con la base de datos en el disco efímero del
    # contenedor, y los datos desaparecían en el siguiente despliegue. Render
    # define RENDER=true por su cuenta en todos sus servicios.
    if os.environ.get("RENDER") and not app.config.get("TESTING"):
        faltan = [k for k in ("SECRET_KEY", "DATABASE_URL") if not os.environ.get(k)]
        if faltan:
            raise RuntimeError(
                "faltan variables de entorno en producción: " + ", ".join(faltan)
            )

    engine = build_engine(app.config["DATABASE_URL"])
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = session_factory

    Base.metadata.create_all(engine)
    # gunicorn arranca dos workers y cada uno ejecuta create_app(): los dos pueden
    # ver las tablas vacías y sembrar a la vez, y el segundo choca contra el índice
    # único de slug. Perder esa carrera es lo normal.
    try:
        with session_factory() as bootstrap:
            seed_database(bootstrap)
    except IntegrityError:
        pass

    @app.before_request
    def open_session() -> None:
        g.db = session_factory()

    @app.teardown_request
    def close_session(exception: BaseException | None) -> None:
        session: Session | None = g.pop("db", None)
        if session is not None:
            session.close()

    @app.after_request
    def cabeceras_de_seguridad(response: Response) -> Response:
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), camera=(), microphone=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; object-src 'none'; base-uri 'none'; "
            "form-action 'self'; frame-ancestors 'none'",
        )
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        # El alias de Render sirve la misma app y no quiero que compita en
        # buscadores con el dominio propio.
        if request.host.endswith(".onrender.com"):
            response.headers.setdefault("X-Robots-Tag", "noindex")
        return response

    @app.context_processor
    def inject_globals() -> dict[str, Any]:
        return {"specialties": SPECIALTIES, "current_year": 2026}

    @app.route("/")
    def index() -> str:
        featured = g.db.scalars(
            select(Creator).order_by(Creator.id).limit(3)
        ).all()
        works = g.db.scalars(select(Work).order_by(Work.id.desc()).limit(3)).all()
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
        return render_template("work.html", work=work, creator=work.creator)

    @app.route("/robots.txt")
    def robots() -> Response:
        sitemap = url_for("sitemap", _external=True)
        body = f"User-agent: *\nAllow: /\nSitemap: {sitemap}\n"
        return Response(body, mimetype="text/plain")

    @app.route("/sitemap.xml")
    def sitemap() -> Response:
        urls = [url_for("index"), url_for("creators")]
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
