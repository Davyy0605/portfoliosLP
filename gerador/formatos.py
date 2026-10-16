"""Formatação de preços e links de WhatsApp."""
import re
from urllib.parse import quote

NUMERO_PROVISORIO = "5500000000000"


def centavos(valor: float) -> int:
    return round(valor * 100)


def brl(valor: float) -> str:
    return "R$ " + f"{centavos(valor) / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def normalizar_whatsapp(numero: str) -> str:
    d = re.sub(r"\D", "", numero)
    if len(d) in (10, 11):
        d = "55" + d
    if len(d) not in (12, 13):
        raise ValueError(f"esperado 12 ou 13 dígitos (com DDD), recebido {numero!r}")
    return d


def link_whatsapp(numero: str, texto: str) -> str:
    return f"https://wa.me/{numero}?text=" + quote(texto, safe="")
