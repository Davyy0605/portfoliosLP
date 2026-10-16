import pytest

from gerador.formatos import NUMERO_PROVISORIO, brl, centavos, link_whatsapp, normalizar_whatsapp
from gerador.qr import qr_svg


def test_brl():
    assert brl(42.9) == "R$ 42,90"
    assert brl(1234.5) == "R$ 1.234,50"
    assert brl(0) == "R$ 0,00"
    assert brl(1234567.891) == "R$ 1.234.567,89"


def test_centavos():
    assert centavos(0.1) + centavos(0.2) == 30


def test_normalizar_whatsapp():
    assert NUMERO_PROVISORIO == "5500000000000"
    assert normalizar_whatsapp("(11) 98765-4321") == "5511987654321"
    assert normalizar_whatsapp("+55 11 98765-4321") == "5511987654321"
    assert normalizar_whatsapp("1187654321") == "551187654321"
    for ruim in ("123", "", "551198765432100"):
        with pytest.raises(ValueError):
            normalizar_whatsapp(ruim)


def test_link_whatsapp():
    url = link_whatsapp("5511987654321", "Olá & tchau 🍔\nok")
    assert url.startswith("https://wa.me/5511987654321?text=")
    assert "%26" in url and "%0A" in url and "%F0%9F%8D%94" in url
    assert " " not in url


def test_qr_svg():
    svg = qr_svg("https://x/")
    assert svg.startswith("<svg") and "<?xml" not in svg and "#1a1a1a" in svg
