"""Ambiente Jinja2 e renderização de sites e do hub."""
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from gerador.dados import ErroDeDados
from gerador.agenda import dados_agendamento
from gerador.formatos import brl, centavos, duracao, link_whatsapp
from gerador.imagens import otimizar_imagens
from gerador.qr import qr_svg


# Segunda página de cada ramo (a primeira é sempre a landing).
PAGINAS = {"gastronomia": "cardapio", "beleza": "agendar"}


def criar_ambiente(raiz: Path) -> Environment:
    env = Environment(loader=FileSystemLoader(Path(raiz) / "temas"), autoescape=True,
                      trim_blocks=True, lstrip_blocks=True)
    env.filters.update(brl=brl, centavos=centavos, duracao=duracao, wa=link_whatsapp)
    return env


def _escrever(env, modelo, caminho: Path, **ctx):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(env.get_template(modelo).render(**ctx), encoding="utf-8")


def _imagens(site, destino: Path, larguras=(800, 1600), arquivos=None, cache: Path | None = None):
    pasta = site["_pasta"] / "imagens"
    if not pasta.is_dir():
        return {}
    return otimizar_imagens(pasta, destino, larguras, arquivos, cache)


def _chave(site) -> Path:
    """sites/<slug> e clientes/<slug> não podem compartilhar cache."""
    return Path(site["_pasta"].parent.name) / site["_pasta"].name


def render_site(env, site: dict, config: dict, destino: Path, raiz_rel: str, url_site: str = "",
                cache: Path | None = None) -> None:
    destino = Path(destino)
    tema = site["site"]["tema"]
    wa = site["contato"]["whatsapp"] or config["whatsapp"]
    ramo = site["site"]["ramo"]
    segunda = PAGINAS[ramo]
    extra = {"agenda": dados_agendamento(site)} if ramo == "beleza" else {}
    # shortcut: imagens duplicadas na segunda página; trocar por prefixo "../" se o deploy pesar.
    paginas = (("landing", destino, raiz_rel, "tema.css"),
               (segunda, destino / segunda, raiz_rel + "../", "../tema.css"))
    for pagina, pasta, raiz, tema_css in paginas:
        imagens = _imagens(site, pasta / "img", cache=cache and Path(cache) / _chave(site))
        _escrever(env, f"{tema}/{pagina}.html", pasta / "index.html", site=site, config=config,
                  imagens=imagens, wa_numero=wa, raiz=raiz, tema_css=tema_css, pagina=pagina, url_site=url_site, **extra)
    shutil.copy(Path(env.loader.searchpath[0]) / tema / "tema.css", destino / "tema.css")


def render_hub(env, sites: list[dict], config: dict, destino: Path, cache: Path | None = None) -> None:
    """Entrada em destino/index.html e uma página por ramo que tenha sites, em destino/<ramo>/."""
    destino = Path(destino)
    por_ramo: dict[str, list[dict]] = {}
    for s in sites:
        ramo = s["site"]["ramo"]
        if ramo not in config["ramos"]:
            raise ErroDeDados(f"{s['site']['slug']}: ramo '{ramo}' sem textos em config.toml [ramos]")
        por_ramo.setdefault(ramo, []).append(s)
    ramos = [{"id": r, **config["ramos"][r], "cards": [], "capa": None}
             for r in config["ramos"] if r in por_ramo]
    for ramo in ramos:
        segunda = PAGINAS[ramo["id"]]
        for s in por_ramo[ramo["id"]]:
            slug = s["site"]["slug"]
            imgs = _imagens(s, destino / "img" / slug, (800,), [s["capa"]["imagem"]],
                            cache and Path(cache) / "hub" / _chave(s))
            capa = imgs.get(s["capa"]["imagem"])
            if capa:  # otimizar_imagens usa o nome da pasta ("<slug>/..."); o hub precisa de "img/<slug>/..."
                capa = {**capa, "src": "img/" + capa["src"],
                        "srcset": ", ".join("img/" + p for p in capa["srcset"].split(", "))}
            ramo["cards"].append({
                "site": s, "capa": capa, "url": f"../{slug}/", "url_secundaria": f"../{slug}/{segunda}/",
                "rotulo_secundaria": "Agendar" if segunda == "agendar" else "Ver cardápio",
                "qr": Markup(qr_svg(f"{config['url_base']}{slug}/{segunda}/"))})
        ramo["capa"] = next((c["capa"] for c in ramo["cards"] if c["capa"]), None)
    _escrever(env, "hub/index.html", destino / "index.html", ramos=ramos, config=config)
    for ramo in ramos:
        _escrever(env, "hub/ramo.html", destino / ramo["id"] / "index.html", ramo=ramo, config=config)
    css = Path(env.loader.searchpath[0]) / "hub" / "hub.css"
    if css.is_file():
        shutil.copy(css, destino / "hub.css")


def copiar_estaticos(raiz: Path, destino: Path) -> None:
    origem = Path(raiz) / "static"
    if origem.is_dir():
        shutil.copytree(origem, Path(destino) / "static", dirs_exist_ok=True)
