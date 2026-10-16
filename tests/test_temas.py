"""Contrato dos temas: cada site de sites/ gera landing + cardápio completos, e o hub lista todos."""
import re
import shutil
from pathlib import Path

import pytest
from PIL import Image

from build import construir_portfolio
from gerador.dados import listar_sites

RAIZ = Path(__file__).parent.parent
SITES = listar_sites(RAIZ / "sites")


def _tema_pronto(s):
    return (RAIZ / "temas" / s["site"]["tema"] / "landing.html").is_file()


@pytest.fixture(scope="module")
def dist(tmp_path_factory):
    """Build do portfólio numa cópia do projeto; temas ainda vazios usam "teste" só para o build passar."""
    base = tmp_path_factory.mktemp("proj")
    for nome in ("temas", "static"):
        shutil.copytree(RAIZ / nome, base / nome)
    shutil.copy(RAIZ / "config.toml", base / "config.toml")
    shutil.copytree(RAIZ / "sites", base / "sites", ignore=shutil.ignore_patterns("*.jpg", "*.jpeg"))
    for jpg in (RAIZ / "sites").glob("*/imagens/*.jp*g"):  # fotos reduzidas: o build leva segundos, não minutos
        with Image.open(jpg) as im:
            im.draft("RGB", (160, 160))
            im = im.convert("RGB")
        im.thumbnail((160, 160))
        im.save(base / jpg.relative_to(RAIZ), quality=60)
    for s in SITES:
        if not _tema_pronto(s):
            toml = base / "sites" / s["site"]["slug"] / "site.toml"
            txt = toml.read_text(encoding="utf-8")
            toml.write_text(re.sub(r'(?m)^tema = ".*"$', 'tema = "teste"', txt, count=1), encoding="utf-8")
    saida = base / "dist"
    construir_portfolio(base, saida)
    return saida


@pytest.mark.parametrize("s", SITES, ids=lambda s: s["site"]["slug"])
def test_tema(dist, s):
    if not _tema_pronto(s):
        pytest.skip(f"temas/{s['site']['tema']}/landing.html ainda não existe")
    slug, modulos = s["site"]["slug"], s["site"]["modulos"]
    landing = (dist / slug / "index.html").read_text(encoding="utf-8")
    cardapio = (dist / slug / "cardapio" / "index.html").read_text(encoding="utf-8")
    for html in (landing, cardapio):
        assert "{{" not in html and "{%" not in html
        for img in re.findall(r"<img\b[^>]*>", html):
            assert "alt=" in img and "width=" in img, img
    assert 'id="contato"' in landing
    assert re.search(r'href="[^"]*cardapio/', landing)
    assert "data-busca" in cardapio
    assert len(re.findall(r"<section\b[^>]*data-categoria", cardapio)) >= 5
    todo = landing + cardapio
    assert ("data-evento" in todo) == ("eventos" in modulos)
    assert ("data-carrinho" in todo) == ("pedido" in modulos)


def test_hub(dist):
    html = (dist / "index.html").read_text(encoding="utf-8")
    cards = re.findall(r'<article class="card".*?</article>', html, re.S)
    assert len(cards) == len(SITES)
    for card, s in zip(cards, SITES):
        assert s["site"]["nome"] in card
        assert "<svg" in card
    assert (dist / "hub.css").is_file()
