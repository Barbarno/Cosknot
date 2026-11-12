from __future__ import annotations

import os
from typing import Any

from flask import Flask, Response, g, render_template, request, url_for
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import Engine
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
        # Neon sirve por pgbouncer en transaction mode: no hay estado de sesion entre
        # transacciones, asi que los prepared statements cacheados por psycopg3 fallan.
        options["connect_args"] = {"sslmode": "require", "prepare_threshold": None}
    return create_engine(url, **options)


def create_app(config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_URL=normalize_database_url(os.environ.get("DATABASE_URL")),
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-not-a-secret"),
        ENV=os.environ.get("FLASK_ENV", "production"),
    )
    if config:
        app.config.update(config)
        app.config["DATABASE_URL"] = normalize_database_url(app.config["DATABASE_URL"])

    engine = build_engine(app.config["DATABASE_URL"])
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    app.extensions["db_engine"] = engine
    app.extensions["db_session"] = session_factory

    Base.metadata.create_all(engine)
    with session_factory() as bootstrap:
        seed_database(bootstrap)

    @app.before_request
    def open_session() -> None:
        g.db = session_factory()

    @app.teardown_request
    def close_session(exception: BaseException | None) -> None:
        session: Session | None = g.pop("db", None)
        if session is not None:
            session.close()

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
        rows = g.db.scalars(select(Creator).order_by(Creator.name)).all()
        return render_template("creators.html", creators=rows)

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
            f"<url><loc>{request.url_root.rstrip('/')}{path}</loc></url>" for path in urls
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

    return app


app = create_app()
