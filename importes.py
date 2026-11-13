"""Formato de importes en céntimos y conversión desde el formulario."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

SIMBOLOS = {"EUR": "€", "USD": "$", "GBP": "£"}


def formato_importe(cents: int | None, currency: str = "EUR") -> str:
    if not cents:
        return "a consultar"
    simbolo = SIMBOLOS.get((currency or "EUR").upper(), (currency or "EUR").upper())
    return f"{cents / 100:.2f} {simbolo}"


def euros_a_centimos(texto: str | None) -> int | None:
    """Convierte «120,50 €» o «120.50» a céntimos. Devuelve None si no es un número."""
    if not texto:
        return None
    limpio = texto.replace("€", "").replace(" ", "").strip().replace(",", ".")
    if not limpio:
        return None
    try:
        valor = Decimal(limpio)
    except InvalidOperation:
        return None
    if valor < 0 or valor > Decimal("1000000"):
        return None
    return int((valor * 100).to_integral_value())
