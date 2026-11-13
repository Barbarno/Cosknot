"""Buzón de avisos que no salieron a la primera.

Un pedido no puede depender de que Resend conteste. El intento se hace dentro de la
petición, con un timeout corto; si falla, el aviso se guarda en `email_outbox` y un
hilo del propio proceso web lo reintenta cada minuto, con espera creciente y un
número máximo de intentos.

Por qué un hilo y no un worker aparte: un worker adicional son 7 $/mes y el
presupuesto son 12. El hilo arranca una sola vez por proceso, vive dentro del dyno
web y no necesita Redis ni cola externa. Lo que no puede pasar es que el estado
viva en memoria: está en la tabla, así que un reinicio del dyno no pierde nada.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from correo import Correo
from models import EmailOutbox

registro = logging.getLogger(__name__)

MAX_INTENTOS_POR_DEFECTO = 5
INTERVALO_SEGUNDOS = 60
LOTE = 20
ESPERA_MAXIMA_MINUTOS = 60


def ahora_utc() -> datetime:
    """Fecha naive en UTC: la base guarda DateTime sin zona en todas las tablas."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def clave_de(destinatario: str, asunto: str, cuerpo: str) -> str:
    """Hash estable del aviso. Dos iguales comparten clave y no se duplican."""
    material = "\x00".join((destinatario.strip(), asunto.strip(), cuerpo))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def encolar(
    sesion: Session,
    destinatario: str,
    asunto: str,
    cuerpo: str,
    ahora: datetime | None = None,
) -> EmailOutbox:
    """Deja el aviso pendiente. Si ya existe con esa clave, devuelve el que hay."""
    if not destinatario:
        raise ValueError("un aviso sin destinatario no se encola")
    momento = ahora or ahora_utc()
    clave = clave_de(destinatario, asunto, cuerpo)

    existente = sesion.scalar(select(EmailOutbox).where(EmailOutbox.clave == clave))
    if existente is not None:
        return existente

    aviso = EmailOutbox(
        clave=clave,
        destinatario=destinatario,
        asunto=asunto,
        cuerpo=cuerpo,
        estado="pendiente",
        intentos=0,
        proximo_intento=momento,
    )
    sesion.add(aviso)
    sesion.flush()
    return aviso


def pendientes(
    sesion: Session, ahora: datetime | None = None, limite: int = LOTE
) -> list[EmailOutbox]:
    """Filas que toca intentar ya, de la más antigua a la más nueva."""
    momento = ahora or ahora_utc()
    consulta = (
        select(EmailOutbox)
        .where(EmailOutbox.estado == "pendiente")
        .where(EmailOutbox.proximo_intento <= momento)
        .order_by(EmailOutbox.id)
        .limit(limite)
    )
    return list(sesion.scalars(consulta))


def _espera(intentos: int) -> timedelta:
    minutos = min(2 ** max(intentos, 0), ESPERA_MAXIMA_MINUTOS)
    return timedelta(minutes=minutos)


def procesar(
    sesion: Session,
    correo: Correo,
    ahora: datetime | None = None,
    limite: int = LOTE,
    max_intentos: int = MAX_INTENTOS_POR_DEFECTO,
) -> dict[str, int]:
    """Intenta enviar lo pendiente. Devuelve el recuento por resultado."""
    resultado = {"enviados": 0, "reintentar": 0, "fallidos": 0}
    if not correo.activo:
        return resultado

    momento = ahora or ahora_utc()
    for aviso in pendientes(sesion, momento, limite):
        if correo.enviar(aviso.destinatario, aviso.asunto, aviso.cuerpo):
            aviso.estado = "enviado"
            aviso.enviado_at = momento
            aviso.ultimo_error = None
            resultado["enviados"] += 1
            continue

        aviso.intentos += 1
        aviso.ultimo_error = "el envío devolvió error"
        if aviso.intentos >= max_intentos:
            aviso.estado = "fallido"
            resultado["fallidos"] += 1
        else:
            aviso.proximo_intento = momento + _espera(aviso.intentos)
            resultado["reintentar"] += 1

    sesion.commit()
    return resultado


_hilo: threading.Thread | None = None
_cerrojo = threading.Lock()


def iniciar_hilo(app, intervalo: int = INTERVALO_SEGUNDOS) -> bool:
    """Arranca el reintento en un hilo del proceso. Solo una vez por proceso.

    Devuelve `True` si este proceso lo ha arrancado y `False` si ya había uno: así
    el arranque es idempotente y no se duplican los envíos.
    """
    global _hilo
    with _cerrojo:
        if _hilo is not None and _hilo.is_alive():
            return False

        hilo = threading.Thread(
            target=_bucle,
            args=(app, intervalo),
            name="email-outbox",
            daemon=True,
        )
        _hilo = hilo
        hilo.start()
        return True


def _bucle(app, intervalo: int) -> None:
    while True:
        time.sleep(intervalo)
        try:
            with app.app_context():
                sesion_factory = app.extensions["db_session"]
                correo = app.extensions.get("correo")
                if correo is None:
                    continue
                max_intentos = int(
                    app.config.get("EMAIL_MAX_INTENTOS") or MAX_INTENTOS_POR_DEFECTO
                )
                with sesion_factory() as sesion:
                    procesar(sesion, correo, max_intentos=max_intentos)
        except Exception as error:  # noqa: BLE001 - el hilo no puede morir por un fallo
            # Un error de base o de red se registra y se espera al siguiente ciclo.
            # Si el hilo muriera, los avisos se quedarían pendientes para siempre.
            registro.warning("el reintento de avisos falló: %s", error)
