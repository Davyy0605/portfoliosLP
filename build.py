"""CLI: python build.py [--site SLUG] [--saida DIR] [--serve [PORTA]]"""
import argparse
import functools
import http.server
import shutil
import sys
from pathlib import Path

from gerador.dados import ErroDeDados, avisos_config, carregar_config, carregar_site, listar_sites
from gerador.render import copiar_estaticos, criar_ambiente, render_hub, render_site

RAIZ = Path(__file__).parent


def _preparar(raiz: Path, saida: Path):
    config = carregar_config(raiz / "config.toml")
    shutil.rmtree(saida, ignore_errors=True)
    saida.mkdir(parents=True)
    copiar_estaticos(raiz, saida)
    return config, criar_ambiente(raiz), avisos_config(config)


def construir_portfolio(raiz: Path, saida: Path) -> list[str]:
    raiz, saida = Path(raiz), Path(saida)
    config, env, avisos = _preparar(raiz, saida)
    pasta = raiz / "sites"
    sites = listar_sites(pasta, raiz / "temas") if pasta.is_dir() else []
    render_hub(env, sites, config, saida)
    for s in sites:
        render_site(env, s, config, saida / s["site"]["slug"], "../")
    return avisos


def construir_cliente(raiz: Path, slug: str, saida: Path) -> list[str]:
    raiz, saida = Path(raiz), Path(saida)
    pasta = next((p for p in (raiz / "clientes" / slug, raiz / "sites" / slug) if p.is_dir()), None)
    if pasta is None:
        raise ErroDeDados(f"{slug}: site não encontrado em clientes/ nem em sites/")
    config, env, avisos = _preparar(raiz, saida)
    render_site(env, carregar_site(pasta, raiz / "temas"), config, saida, "")
    return avisos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Gera landing pages e cardápios digitais.")
    ap.add_argument("--site", metavar="SLUG")
    ap.add_argument("--saida", default="dist")
    ap.add_argument("--serve", nargs="?", const=8000, type=int, metavar="PORTA")
    a = ap.parse_args(argv)
    saida = Path(a.saida)
    try:
        avisos = construir_cliente(RAIZ, a.site, saida) if a.site else construir_portfolio(RAIZ, saida)
    except ErroDeDados as e:
        print(e, file=sys.stderr)
        return 1
    for av in avisos:
        print(f"AVISO: {av}")
    if a.serve is not None:
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(saida))
        print(f"Servindo {saida} em http://localhost:{a.serve}/")
        try:
            http.server.ThreadingHTTPServer(("", a.serve), h).serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
