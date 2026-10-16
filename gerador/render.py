"""Ambiente Jinja2 e renderização de sites e do hub."""
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from gerador.formatos import brl, centavos, link_whatsapp
from gerador.imagens import otimizar_imagens
from gerador.qr import qr_svg


def criar_ambiente(raiz: Path) -> Environment:
    env = Environment(loader=FileSystemLoader(Path(raiz) / "temas"), autoescape=True,
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(brl=brl, centavos=centavos, wa=link_whatsapp)
    return env


def _escrever(env, modelo, caminho: Path, **ctx):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(env.get_template(modelo).render(**ctx), encoding="utf-8")


def _imagens(site, destino: Path, larguras=(800, 1600)):
    pasta = site["_pasta"] / "imagens"
    return otimizar_imagens(pasta, destino, larguras) if pasta.is_dir() else {}


def render_site(env, site: dict, config: dict, destino: Path, raiz_rel: str) -> None:
    destino = Path(destino)
    tema = site["site"]["tema"]
    wa = site["contato"]["whatsapp"] or config["whatsapp"]
    # shortcut: imagens duplicadas no cardápio; trocar por prefixo "../" se o deploy pesar.
    paginas = (("landing", destino, raiz_rel, "tema.css", "index.html"),
               ("cardapio", destino / "cardapio", raiz_rel + "../", "../tema.css", "cardapio/index.html"))
    for pagina, pasta, raiz, tema_css, _ in paginas:
        imagens = _imagens(site, pasta / "img")
        _escrever(env, f"{tema}/{pagina}.html", pasta / "index.html", site=site, config=config,
                  imagens=imagens, wa_numero=wa, raiz=raiz, tema_css=tema_css, pagina=pagina)
    css = env.loader.searchpath[0]
    shutil.copy(Path(css) / tema / "tema.css", destino / "tema.css")


def render_hub(env, sites: list[dict], config: dict, destino: Path) -> None:
    destino = Path(destino)
    cards = []
    for s in sites:
        slug = s["site"]["slug"]
        imgs = _imagens(s, destino / "img" / slug, (800,))
        capa = imgs.get(s["capa"]["imagem"])
        if capa:  # otimizar_imagens usa o nome da pasta ("<slug>/..."); o hub precisa de "img/<slug>/..."
            capa = {**capa, "src": "img/" + capa["src"],
                    "srcset": ", ".join("img/" + p for p in capa["srcset"].split(", "))}
        cards.append({"site": s, "url": f"{slug}/", "url_cardapio": f"{slug}/cardapio/",
                      "qr": Markup(qr_svg(f"{config['url_base']}{slug}/cardapio/")), "capa": capa})
    _escrever(env, "hub/index.html", destino / "index.html", cards=cards, config=config)
    css = Path(env.loader.searchpath[0]) / "hub" / "hub.css"
    if css.is_file():
        shutil.copy(css, destino / "hub.css")


def copiar_estaticos(raiz: Path, destino: Path) -> None:
    origem = Path(raiz) / "static"
    if origem.is_dir():
        shutil.copytree(origem, Path(destino) / "static", dirs_exist_ok=True)
