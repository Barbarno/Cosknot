"""Plan de despliegue en Heroku: orden de comandos, sin tocar nada real."""

from __future__ import annotations

from scripts.desplegar_heroku import (
    SECRETOS_GITHUB,
    VARIABLES_BASE,
    formatear,
    generar_secret_key,
    plan,
    plan_secretos_github,
    variables_del_entorno,
)


def comandos_en_plano(comandos):
    return [" ".join(comando) for comando in comandos]


def test_la_secret_key_son_64_hex_y_no_se_repite():
    una = generar_secret_key()
    otra = generar_secret_key()
    assert len(una) == 64
    int(una, 16)
    assert una != otra


def test_el_orden_respeta_las_dependencias():
    plano = comandos_en_plano(plan(existe_app=False, existe_addon=False))
    # app -> addon -> config -> dominios -> certificado -> push -> sembrar
    assert plano[0].startswith("heroku create cosknot --region eu")
    assert plano[1].startswith("heroku addons:create heroku-postgresql:essential-0")
    assert "--app cosknot --wait" in plano[1]
    assert plano[2].startswith("heroku config:set")
    assert "domains:add cosknot.es" in plano[3]
    assert "domains:add www.cosknot.es" in plano[4]
    assert plano[5] == "heroku certs:auto:enable --app cosknot"
    assert plano[6] == "git push heroku main"
    assert plano[7].startswith("heroku run flask sembrar")


def test_si_la_app_ya_existe_no_se_crea_otra_vez():
    plano = comandos_en_plano(plan(existe_app=True, existe_addon=True))
    assert not any(linea.startswith("heroku create") for linea in plano)
    assert not any("addons:create" in linea for linea in plano)
    assert plano[0].startswith("heroku config:set")


def test_las_config_vars_llevan_los_numeros_del_plan():
    comando = plan(existe_app=True, existe_addon=True, secret_key="k" * 64)[0]
    assert comando[:3] == ["heroku", "config:set", "--app"]
    texto = " ".join(comando)
    assert "SECRET_KEY=" + "k" * 64 in texto
    for nombre, valor in VARIABLES_BASE.items():
        assert f"{nombre}={valor}" in texto
    # el pool nunca puede pasar del reparto 8/20 documentado
    assert int(VARIABLES_BASE["DB_POOL_SIZE"]) + int(
        VARIABLES_BASE["DB_MAX_OVERFLOW"]
    ) == 5


def test_las_opcionales_entran_solo_si_estan():
    entorno = {"R2_BUCKET": "cosknot", "RESEND_API_KEY": "  ", "GEMINI_MODEL": "m"}
    presentes = variables_del_entorno(entorno)
    assert presentes == {"R2_BUCKET": "cosknot", "GEMINI_MODEL": "m"}

    comando = plan(
        existe_app=True,
        existe_addon=True,
        secret_key="k" * 64,
        opcionales=presentes,
    )[0]
    texto = " ".join(comando)
    assert "R2_BUCKET=cosknot" in texto
    assert "RESEND_API_KEY" not in texto


def test_sin_dominio_www_no_se_duplica():
    plano = comandos_en_plano(plan(dominio="www.cosknot.es", existe_app=True))
    assert sum("domains:add" in linea for linea in plano) == 1


def test_se_puede_saltar_la_siembra():
    plano = comandos_en_plano(plan(sembrar=False))
    assert not any("sembrar" in linea for linea in plano)


def test_los_secretos_de_github_solo_van_si_hay_valor():
    comandos = plan_secretos_github(
        "cosknot", entorno={"R2_BUCKET": "cosknot", "BACKUP_PASSPHRASE": ""}
    )
    nombres = [comando[3] for comando in comandos]
    # HEROKU_APP_NAME se rellena con el nombre de la app; el resto, solo si hay valor
    assert nombres == ["HEROKU_APP_NAME", "R2_BUCKET"]
    assert comandos[0][-1] == "cosknot"


def test_ningun_secreto_de_github_se_imprime():
    comandos = plan_secretos_github("cosknot", entorno={"R2_BUCKET": "mi-bucket"})
    lineas = formatear(comandos)
    # el nombre del secreto se ve; el valor, nunca
    assert lineas[0] == "gh secret set HEROKU_APP_NAME --body <oculto>"
    assert lineas[1] == "gh secret set R2_BUCKET --body <oculto>"
    assert not any("mi-bucket" in linea for linea in lineas)


def test_la_secret_key_se_recorta_al_imprimir():
    comando = plan(existe_app=True, existe_addon=True, secret_key="a" * 64)[0]
    lineas = formatear([comando], ocultar=("SECRET_KEY",))
    assert "a" * 64 not in lineas[0]
    assert "SECRET_KEY=aaaa...(64 caracteres)" in lineas[0]


def test_la_lista_de_secretos_cubre_los_flujos():
    assert set(SECRETOS_GITHUB) == {
        "HEROKU_APP_NAME",
        "BACKUP_PASSPHRASE",
        "R2_ENDPOINT_URL",
        "R2_BUCKET",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
    }
