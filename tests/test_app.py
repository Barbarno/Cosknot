from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app import build_engine, create_app, normalize_database_url
from models import Creator, Work
from seed import SEED_CREATORS


@pytest.fixture()
def app(tmp_path):
    db_path = tmp_path / "test.db"
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{db_path.as_posix()}",
            "SECRET_KEY": "test-key",
        }
    )
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def test_normalize_database_url():
    assert normalize_database_url(None) == "sqlite:///cosknot.db"
    assert normalize_database_url("") == "sqlite:///cosknot.db"
    assert normalize_database_url("sqlite:///x.db") == "sqlite:///x.db"
    assert (
        normalize_database_url("postgres://u:p@host/db")
        == "postgresql+psycopg://u:p@host/db"
    )
    assert (
        normalize_database_url("postgresql://u:p@host/db")
        == "postgresql+psycopg://u:p@host/db"
    )
    assert (
        normalize_database_url("postgresql+psycopg://u:p@host/db")
        == "postgresql+psycopg://u:p@host/db"
    )


def test_engine_options_differ_by_backend():
    sqlite_engine = build_engine("sqlite:///x.db")
    assert sqlite_engine.dialect.name == "sqlite"
    assert sqlite_engine.pool._pre_ping is False
    assert "sslmode" not in (sqlite_engine.dialect.create_connect_args(sqlite_engine.url)[1] or {})

    pg_engine = build_engine("postgresql+psycopg://u:p@localhost/db")
    assert pg_engine.dialect.name == "postgresql"
    assert pg_engine.pool._pre_ping is True


def test_index_renders_landing(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "descubrir creadores" in body
    assert "cómo funciona" in body
    assert "/creadores" in body


def test_creators_index_lists_seeded_creators(client):
    response = client.get("/creadores")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert body.count('class="card creator-card"') == len(SEED_CREATORS)
    for specialty in ("ropa", "props", "accesorios"):
        assert f'data-filter="{specialty}"' in body
    assert 'data-specialty="ropa"' in body


def test_creator_profile_shows_bio_and_works(client, app):
    slug = SEED_CREATORS[0]["slug"]
    response = client.get(f"/creadores/{slug}")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert SEED_CREATORS[0]["name"] in body
    assert SEED_CREATORS[0]["bio"][:60] in body
    for work in SEED_CREATORS[0]["works"]:
        assert work["title"] in body
        assert f"/obras/{work['slug']}" in body


def test_work_detail_shows_price_status_and_mailto(client):
    creator = SEED_CREATORS[0]
    work = creator["works"][1]
    response = client.get(f"/obras/{work['slug']}")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert work["title"] in body
    assert work["description"] in body
    assert work["price_note"] in body
    assert work["status"] in body
    assert f"mailto:{creator['contact_email']}" in body
    assert f"/creadores/{creator['slug']}" in body


def test_work_without_price_falls_back_to_consult(client):
    creator = next(c for c in SEED_CREATORS if any(w["price_note"] is None for w in c["works"]))
    work = next(w for w in creator["works"] if w["price_note"] is None)
    response = client.get(f"/obras/{work['slug']}")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "a consultar" in body


def test_healthz_reports_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_unknown_routes_render_custom_404(client):
    for path in ("/no-existe", "/creadores/no-existe", "/obras/no-existe"):
        response = client.get(path)
        assert response.status_code == 404
        body = response.get_data(as_text=True)
        assert "esta página no existe" in body
        assert "/creadores" in body


def test_seed_is_idempotent(app):
    factory = app.extensions["db_session"]
    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Creator)) == len(SEED_CREATORS)
        works_per_creator = session.execute(
            select(Work.creator_id, func.count()).group_by(Work.creator_id)
        ).all()
    assert all(2 <= count <= 3 for _, count in works_per_creator)

    create_app(
        {
            "TESTING": True,
            "DATABASE_URL": app.config["DATABASE_URL"],
            "SECRET_KEY": "test-key",
        }
    )

    with factory() as session:
        assert session.scalar(select(func.count()).select_from(Creator)) == len(SEED_CREATORS)
