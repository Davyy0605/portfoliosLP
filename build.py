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


MARCADOR = ".gerado-por-build"


def _preparar(raiz: Path, saida: Path) -> None:
    """Apaga e recria a saída, recusando diretórios que não são saída do build."""
    r, s = raiz.resolve(), saida.resolve()
    if s == r or s in r.parents or any((s / n).exists() for n in ("config.toml", "sites", "temas")):
        raise ErroDeDados(f"--saida {saida}: recusado, o diretório contém o projeto")
    if s.exists():
        if not s.is_dir() or (any(s.iterdir()) and not (s / MARCADOR).is_file()):
            raise ErroDeDados(f"--saida {saida}: recusado, diretório não vazio que não foi gerado pelo build")
        try:
            shutil.rmtree(s)
        except OSError as e:
            raise ErroDeDados(f"--saida {saida}: não foi possível apagar ({e.strerror or e})") from None
    s.mkdir(parents=True)
    (s / MARCADOR).write_text("", encoding="utf-8")
    copiar_estaticos(raiz, s)


def construir_portfolio(raiz: Path, saida: Path) -> list[str]:
    raiz, saida = Path(raiz), Path(saida)
    config = carregar_config(raiz / "config.toml")
    pasta = raiz / "sites"
    sites = listar_sites(pasta, raiz / "temas") if pasta.is_dir() else []
    _preparar(raiz, saida)
    env = criar_ambiente(raiz)
    render_hub(env, sites, config, saida)
    for s in sites:
        slug = s["site"]["slug"]
        render_site(env, s, config, saida / slug, "../", config["url_base"] + slug + "/")
    return avisos_config(config)


def construir_cliente(raiz: Path, slug: str, saida: Path) -> list[str]:
    raiz, saida = Path(raiz), Path(saida)
    pasta = next((p for p in (raiz / "clientes" / slug, raiz / "sites" / slug) if p.is_dir()), None)
    if pasta is None:
        raise ErroDeDados(f"{slug}: site não encontrado em clientes/ nem em sites/")
    config = carregar_config(raiz / "config.toml")
    site = carregar_site(pasta, raiz / "temas")
    _preparar(raiz, saida)
    render_site(criar_ambiente(raiz), site, config, saida, "", config["url_base"])
    return avisos_config(config)


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
            http.server.ThreadingHTTPServer(("127.0.0.1", a.serve), h).serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
