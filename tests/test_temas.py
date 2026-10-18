"""Contrato dos temas: cada site de sites/ gera landing + cardápio completos, e o hub lista todos."""
import contextlib
import functools
import http.server
import re
import shutil
import threading
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


PAGINAS = {"gastronomia": "cardapio", "beleza": "agendar"}


def _ramos_com_sites():
    return [r for r in PAGINAS if any(s["site"]["ramo"] == r for s in SITES)]


@pytest.mark.parametrize("s", SITES, ids=lambda s: s["site"]["slug"])
def test_tema(dist, s):
    if not _tema_pronto(s):
        pytest.skip(f"temas/{s['site']['tema']}/landing.html ainda não existe")
    slug, modulos, ramo = s["site"]["slug"], s["site"]["modulos"], s["site"]["ramo"]
    segunda = PAGINAS[ramo]
    landing = (dist / slug / "index.html").read_text(encoding="utf-8")
    interna = (dist / slug / segunda / "index.html").read_text(encoding="utf-8")
    for html in (landing, interna):
        assert "{{" not in html and "{%" not in html
        for img in re.findall(r"<img\b[^>]*>", html):
            assert "alt=" in img and "width=" in img, img
    assert 'id="contato"' in landing
    assert re.search(rf'href="[^"]*{segunda}/', landing)
    todo = landing + interna
    if ramo == "gastronomia":
        assert "data-busca" in interna
        assert len(re.findall(r"<section\b[^>]*data-categoria", interna)) >= 5
        assert ("data-evento" in todo) == ("eventos" in modulos)
        assert ("data-carrinho" in todo) == ("pedido" in modulos)
    else:
        assert len(re.findall(r"data-servico", interna)) >= 4
        assert "data-agendamento" in interna


def test_hub(dist):
    entrada = (dist / "index.html").read_text(encoding="utf-8")
    ramos = _ramos_com_sites()
    for ramo in PAGINAS:
        assert (f'href="{ramo}/"' in entrada) == (ramo in ramos)
        assert (dist / ramo / "index.html").is_file() == (ramo in ramos)
    for ramo in ramos:
        html = (dist / ramo / "index.html").read_text(encoding="utf-8")
        cards = re.findall(r'<article class="card".*?</article>', html, re.S)
        esperados = [s for s in SITES if s["site"]["ramo"] == ramo]
        assert len(cards) == len(esperados)
        for card, s in zip(cards, esperados):
            assert s["site"]["nome"] in card
            assert "<svg" in card
    assert (dist / "hub.css").is_file()


@contextlib.contextmanager
def _servir(pasta):
    """http.server local com fila de conexões grande: o padrão (5) estourava quando o chromium abre dezenas de
    conexões paralelas por página, e o reset virava "Navigation interrupted by chrome-error" no Windows."""
    class Quieto(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def handle(self):
            try:
                super().handle()
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass  # o navegador cancelou a requisição (ex.: imagem fora da tela): não é erro do servidor

    class Servidor(http.server.ThreadingHTTPServer):
        request_queue_size = 128
        daemon_threads = True

    srv = Servidor(("127.0.0.1", 0), functools.partial(Quieto, directory=str(pasta)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_port}/"
    finally:
        srv.shutdown()
        srv.server_close()


@pytest.fixture(scope="module")
def navegador(dist):
    """Um servidor e um chromium para o módulo todo; subir e derrubar a cada teste deixava requisições em voo."""
    sync_api = pytest.importorskip("playwright.sync_api")
    with _servir(dist) as base, sync_api.sync_playwright() as p:
        try:
            nav = p.chromium.launch()
        except Exception as e:  # chromium não instalado
            pytest.skip(f"chromium do Playwright indisponível: {e}")
        yield base, nav
        nav.close()


def _abrir(ctx, pagina, url):
    """Navega; se a carga for interrompida, repete numa página nova (a antiga fica presa em chrome-error)."""
    for tentativa in (1, 2, 3):
        try:
            pagina.goto(url, wait_until="load", timeout=60000)
            pagina.evaluate("document.fonts.ready")
            return pagina
        except Exception:
            if tentativa == 3:
                raise
            pagina.close()
            pagina = ctx.new_page()


@pytest.mark.parametrize("largura,altura", [(390, 844), (720, 360), (844, 390), (1024, 768), (1440, 900)])
def test_sem_rolagem_lateral(navegador, largura, altura):
    """Celular em pé, deitado, tablet e desktop: nenhuma página pode ficar mais larga que a tela."""
    base, nav = navegador
    ctx = nav.new_context(viewport={"width": largura, "height": altura}, reduced_motion="reduce")
    # só o servidor local: fontes/mapas externos não são o assunto e deixavam conexões penduradas
    ctx.route(lambda u: not u.startswith(base), lambda r: r.abort())
    pagina = ctx.new_page()
    urls = [base + hub for hub in ["", *(f"{r}/" for r in _ramos_com_sites())]]
    urls += [f"{base}{s['site']['slug']}/{sub}" for s in SITES for sub in ("", PAGINAS[s["site"]["ramo"]] + "/")]
    largas = []
    try:
        for url in urls:
            pagina = _abrir(ctx, pagina, url)
            sw, cw = pagina.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")
            if sw > cw:
                largas.append(f"{url.removeprefix(base) or '/'} ({sw}>{cw})")
    finally:
        ctx.close()
    assert not largas
