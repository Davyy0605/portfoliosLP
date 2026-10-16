"""Capturas de tela para QA visual.

Uso: python ferramentas/capturar.py <url ou pasta dist> <saida_png_dir>
Grava <slug>-<pagina>-<largura>.png (hub: hub-index) em 390x844 e 1440x900, página inteira.
"""
import contextlib
import functools
import http.server
import re
import sys
import threading
import urllib.request
from pathlib import Path

TAMANHOS = {390: 844, 1440: 900}


@contextlib.contextmanager
def servir(pasta):
    """Sobe um http.server temporário em 127.0.0.1 numa porta livre; devolve a URL base."""
    class Quieto(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    h = functools.partial(Quieto, directory=str(pasta))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{srv.server_port}/"
    finally:
        srv.shutdown()
        srv.server_close()


def paginas(base):
    """Lista (slug, pagina, caminho) a partir do hub; sem links, trata a raiz como um site de cliente."""
    html = urllib.request.urlopen(base).read().decode("utf-8", "replace")
    slugs = sorted(set(re.findall(r'href="([\w-]+)/"', html)) - {"static", "img"})
    if not slugs:
        return [("site", "landing", ""), ("site", "cardapio", "cardapio/")]
    res = [("hub", "index", "")]
    for s in slugs:
        res += [(s, "landing", f"{s}/"), (s, "cardapio", f"{s}/cardapio/")]
    return res


def capturar(base, saida):
    from playwright.sync_api import sync_playwright

    saida = Path(saida)
    saida.mkdir(parents=True, exist_ok=True)
    gravados = []
    with sync_playwright() as p:
        nav = p.chromium.launch()
        try:
            for largura, altura in TAMANHOS.items():
                pagina = nav.new_page(viewport={"width": largura, "height": altura})
                for slug, nome, caminho in paginas(base):
                    # "networkidle" nunca chega com o iframe do Google Maps
                    pagina.goto(base + caminho, wait_until="load")
                    pagina.evaluate("document.fonts.ready")
                    arq = saida / f"{slug}-{nome}-{largura}.png"
                    pagina.screenshot(path=str(arq), full_page=True)
                    gravados.append(arq)
                pagina.close()
        finally:
            nav.close()
    return gravados


def main(argv=None):
    a = sys.argv[1:] if argv is None else argv
    if len(a) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    alvo, saida = a
    if alvo.startswith(("http://", "https://")):
        gravados = capturar(alvo if alvo.endswith("/") else alvo + "/", saida)
    else:
        if not Path(alvo).is_dir():
            print(f"{alvo}: pasta não encontrada", file=sys.stderr)
            return 1
        with servir(alvo) as base:
            gravados = capturar(base, saida)
    print(f"{len(gravados)} capturas em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
