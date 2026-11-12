"""Comprueba que la base de datos configurada en DATABASE_URL responde y tiene datos."""
import os

from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://")
engine = create_engine(url, connect_args={"sslmode": "require"}, pool_pre_ping=True)

with engine.connect() as conn:
    tablas = [r[0] for r in conn.execute(text("select tablename from pg_tables where schemaname='public' order by 1"))]
    print("tablas:", tablas)
    for tabla in ("creators", "works"):
        if tabla in tablas:
            print(tabla, conn.execute(text(f"select count(*) from {tabla}")).scalar())
