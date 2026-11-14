"""Registros DNS en Cloudflare: plan idempotente, sin red."""

from __future__ import annotations

import io
import json

import pytest

from scripts.dns_cloudflare import (
    ErrorCloudflare,
    leer_fichero,
    normalizar,
    plan,
    registros_existentes,
    zona_id,
)


class RespuestaFalsa(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
        return False


def abridor(respuestas):
    """Devuelve un `abrir` que sirve las respuestas en orden y apunta las rutas."""
    pendientes = list(respuestas)
    vistas: list[tuple[str, str]] = []

    def abrir(peticion, timeout=None):
        vistas.append((peticion.get_method(), peticion.full_url))
        cuerpo = pendientes.pop(0)
        return RespuestaFalsa(json.dumps(cuerpo).encode("utf-8"))

    abrir.vistas = vistas
    return abrir


def test_el_nombre_se_normaliza_a_fqdn():
    assert normalizar("@", "cosknot.me") == "cosknot.me"
    assert normalizar("", "cosknot.me") == "cosknot.me"
    assert normalizar("send", "cosknot.me") == "send.cosknot.me"
    # no duplica el dominio si ya viene completo
    assert normalizar("send.cosknot.me", "cosknot.me") == "send.cosknot.me"


def test_saca_el_id_de_la_zona():
    abrir = abridor([{"success": True, "result": [{"id": "abc123"}]}])
    assert zona_id("cosknot.me", "token", abrir=abrir) == "abc123"
    assert abrir.vistas[0][1].endswith("/zones?name=cosknot.me")


def test_si_el_token_no_ve_la_zona_lo_dice():
    abrir = abridor([{"success": True, "result": []}])
    with pytest.raises(ErrorCloudflare) as error:
        zona_id("cosknot.me", "token", abrir=abrir)
    assert "Zone:Read" in str(error.value)


def test_sin_token_no_se_llama_a_la_api():
    with pytest.raises(ErrorCloudflare) as error:
        zona_id("cosknot.me", "  ")
    assert "CLOUDFLARE_API_TOKEN" in str(error.value)


def test_plan_omite_lo_que_ya_esta_igual():
    deseados = [
        {"type": "TXT", "name": "resend._domainkey", "content": "p=abc", "ttl": 1},
        {"type": "CNAME", "name": "send", "content": "send.for.mta.net", "ttl": 1},
    ]
    existentes = [
        {
            "type": "TXT",
            "name": "resend._domainkey.cosknot.me",
            "content": "p=abc",
        }
    ]
    crear, omitir = plan(deseados, existentes, "cosknot.me")
    assert [r["name"] for r in omitir] == ["resend._domainkey"]
    assert [r["name"] for r in crear] == ["send.cosknot.me"]


def test_plan_crea_si_cambia_el_contenido():
    deseados = [{"type": "TXT", "name": "@", "content": "nuevo", "ttl": 1}]
    existentes = [{"type": "TXT", "name": "cosknot.me", "content": "viejo"}]
    crear, omitir = plan(deseados, existentes, "cosknot.me")
    assert not omitir
    assert crear[0]["name"] == "cosknot.me"


def test_todo_se_crea_sin_proxy(tmp_path):
    ruta = tmp_path / "registros.json"
    ruta.write_text(
        json.dumps(
            [
                {"type": "cname", "name": "@", "content": "app.herokuapp.com"},
                {"type": "TXT", "name": "_dmarc", "content": "v=DMARC1; p=none;"},
            ]
        ),
        "utf-8",
    )
    deseados = leer_fichero(str(ruta))
    assert all(registro["proxied"] is False for registro in deseados)
    assert deseados[0]["type"] == "CNAME"


def test_un_registro_sin_contenido_no_vale(tmp_path):
    ruta = tmp_path / "mal.json"
    ruta.write_text(json.dumps([{"type": "TXT", "name": "send", "content": " "}]), "utf-8")
    with pytest.raises(ErrorCloudflare) as error:
        leer_fichero(str(ruta))
    assert "content" in str(error.value)


def test_un_tipo_raro_no_vale(tmp_path):
    ruta = tmp_path / "raro.json"
    ruta.write_text(json.dumps([{"type": "SRV", "name": "x", "content": "y"}]), "utf-8")
    with pytest.raises(ErrorCloudflare):
        leer_fichero(str(ruta))


def test_la_lista_de_registros_se_lee_del_fichero(tmp_path):
    ruta = tmp_path / "ok.json"
    ruta.write_text(
        json.dumps(
            [
                {"type": "TXT", "name": "resend._domainkey", "content": "p=MIGf"},
                {"type": "CNAME", "name": "rsend", "content": "rsend-eu.mta.net"},
            ]
        ),
        "utf-8",
    )
    registros = leer_fichero(str(ruta))
    assert len(registros) == 2
    assert registros[0]["ttl"] == 1


def test_los_existentes_se_piden_paginados():
    abrir = abridor([{"success": True, "result": [{"id": "1", "type": "TXT"}]}])
    assert registros_existentes("zona1", "token", abrir=abrir)[0]["id"] == "1"
    assert "per_page=100" in abrir.vistas[0][1]
