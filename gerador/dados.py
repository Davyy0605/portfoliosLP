"""Leitura e validação de config.toml e site.toml."""
import datetime
import re
import tomllib
from pathlib import Path

PROVISORIO = "5500000000000"
MODULOS = {"eventos", "pedido"}
SELOS = {"vegano", "vegetariano", "sem-gluten", "picante", "novo", "chef"}
CTAS = {"cardapio", "reservar", "pedir"}


class ErroDeDados(Exception):
    """Mensagem: '<arquivo>: <campo>: <problema>'."""


class _V:
    """Validador ligado a um arquivo; cada método recebe o caminho do campo."""

    def __init__(self, arquivo, pasta_imagens=None):
        self.arquivo, self.pasta_imagens = arquivo, pasta_imagens

    def erro(self, caminho, problema):
        return ErroDeDados(f"{self.arquivo}: {caminho}: {problema}")

    def _pegar(self, d, chave, caminho, padrao, obrigatorio):
        if chave not in d:
            if obrigatorio:
                raise self.erro(caminho, "campo obrigatório ausente")
            return padrao
        return d[chave]

    def texto(self, d, chave, caminho, padrao="", obrigatorio=False):
        v = self._pegar(d, chave, caminho, padrao, obrigatorio)
        if not isinstance(v, str):
            raise self.erro(caminho, f"esperado texto, recebido {v!r}")
        if obrigatorio and not v.strip():
            raise self.erro(caminho, "não pode ser vazio")
        return v

    def numero(self, d, chave, caminho, padrao=None, obrigatorio=False, inteiro=False):
        v = self._pegar(d, chave, caminho, padrao, obrigatorio)
        if v is None:
            return None
        tipos = (int,) if inteiro else (int, float)
        if isinstance(v, bool) or not isinstance(v, tipos) or v < 0:
            raise self.erro(caminho, f"esperado número{' inteiro' if inteiro else ''} não negativo, recebido {v!r}")
        return v

    def lista(self, d, chave, caminho, obrigatorio=False):
        v = self._pegar(d, chave, caminho, [], obrigatorio)
        if not isinstance(v, list):
            raise self.erro(caminho, "esperada uma lista")
        return v

    def tabela(self, d, chave, caminho):
        v = d.get(chave, {})
        if not isinstance(v, dict):
            raise self.erro(caminho, "esperada uma tabela")
        return v

    def item_tabela(self, v, caminho):
        if not isinstance(v, dict):
            raise self.erro(caminho, "esperada uma tabela")
        return v

    def escolhas(self, d, chave, caminho, validos):
        res = []
        for i, v in enumerate(self.lista(d, chave, caminho)):
            if v not in validos:
                raise self.erro(f"{caminho}[{i}]", f"valor {v!r} inválido; use um de {sorted(validos)}")
            res.append(v)
        return res

    def arquivo_imagem(self, nome, caminho):
        if nome and self.pasta_imagens is not None and not (self.pasta_imagens / nome).is_file():
            raise self.erro(caminho, f"imagem {nome!r} não encontrada em imagens/")

    def imagem(self, d, chave, caminho):
        nome = self.texto(d, chave, caminho)
        self.arquivo_imagem(nome, caminho)
        return nome

    def imagens(self, d, chave, caminho):
        res = []
        for i, nome in enumerate(self.lista(d, chave, caminho)):
            if not isinstance(nome, str):
                raise self.erro(f"{caminho}[{i}]", f"esperado texto, recebido {nome!r}")
            self.arquivo_imagem(nome, f"{caminho}[{i}]")
            res.append(nome)
        return res


def _ler(caminho: Path, rotulo: str) -> dict:
    try:
        with open(caminho, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        raise ErroDeDados(f"{rotulo}: arquivo não encontrado") from None
    except tomllib.TOMLDecodeError as e:
        raise ErroDeDados(f"{rotulo}: TOML inválido: {e}") from None


def carregar_config(caminho: Path) -> dict:
    v = _V("config.toml")
    bruto = _ler(caminho, "config.toml")
    marca = v.tabela(bruto, "marca", "marca")
    zap = v.texto(bruto, "whatsapp", "whatsapp", obrigatorio=True)
    # Task 2 troca por normalizar_whatsapp
    digitos = re.sub(r"\D", "", zap)
    if len(digitos) not in (12, 13):
        raise v.erro("whatsapp", f"esperado 12 ou 13 dígitos, recebido {zap!r}")
    url = v.texto(bruto, "url_base", "url_base", obrigatorio=True)
    return {
        "marca": {
            "nome": v.texto(marca, "nome", "marca.nome", obrigatorio=True),
            "cor": v.texto(marca, "cor", "marca.cor", obrigatorio=True),
        },
        "whatsapp": digitos,
        "url_base": url if url.endswith("/") else url + "/",
    }


def avisos_config(config: dict) -> list[str]:
    if config["whatsapp"] == PROVISORIO:
        return [f"config.toml: whatsapp ainda é o número provisório {PROVISORIO}"]
    return []


def carregar_site(pasta: Path, temas_dir: Path | None = None) -> dict:
    pasta = Path(pasta)
    if temas_dir is None:
        temas_dir = pasta.parent.parent / "temas"
    v = _V(f"{pasta.parent.name}/{pasta.name}/site.toml", pasta / "imagens")
    bruto = _ler(pasta / "site.toml", v.arquivo)

    if "site" not in bruto:
        raise v.erro("site", "tabela obrigatória ausente")
    s = v.tabela(bruto, "site", "site")
    slug = v.texto(s, "slug", "site.slug", obrigatorio=True)
    if slug != pasta.name:
        raise v.erro("site.slug", f"{slug!r} deve ser igual ao nome da pasta {pasta.name!r}")
    tema = v.texto(s, "tema", "site.tema", obrigatorio=True)
    if not (Path(temas_dir) / tema).is_dir():
        raise v.erro("site.tema", f"tema {tema!r} não existe em temas/")
    site = {
        "slug": slug, "tema": tema,
        "nome": v.texto(s, "nome", "site.nome", obrigatorio=True),
        "segmento": v.texto(s, "segmento", "site.segmento", obrigatorio=True),
        "ordem": v.numero(s, "ordem", "site.ordem", 99, inteiro=True),
        "slogan": v.texto(s, "slogan", "site.slogan"),
        "descricao": v.texto(s, "descricao", "site.descricao"),
        "modulos": v.escolhas(s, "modulos", "site.modulos", MODULOS),
        "cor": v.texto(s, "cor", "site.cor"),
    }

    c = v.tabela(bruto, "contato", "contato")
    contato = {k: v.texto(c, k, f"contato.{k}") for k in
               ("whatsapp", "telefone", "instagram", "endereco", "mapa_url")}

    horarios = []
    for i, h in enumerate(v.lista(bruto, "horarios", "horarios")):
        p = f"horarios[{i}]"
        h = v.item_tabela(h, p)
        horarios.append({"dias": v.texto(h, "dias", f"{p}.dias", obrigatorio=True),
                         "horas": v.texto(h, "horas", f"{p}.horas", obrigatorio=True)})

    k = v.tabela(bruto, "capa", "capa")
    cta = v.texto(k, "cta", "capa.cta", "cardapio")
    if cta not in CTAS:
        raise v.erro("capa.cta", f"{cta!r} inválido; use um de {sorted(CTAS)}")
    capa = {"titulo": v.texto(k, "titulo", "capa.titulo"), "subtitulo": v.texto(k, "subtitulo", "capa.subtitulo"),
            "imagem": v.imagem(k, "imagem", "capa.imagem"), "cta": cta}

    so = v.tabela(bruto, "sobre", "sobre")
    sobre = {"titulo": v.texto(so, "titulo", "sobre.titulo"), "texto": v.texto(so, "texto", "sobre.texto"),
             "imagens": v.imagens(so, "imagens", "sobre.imagens")}

    destaques = []
    for i, d in enumerate(v.lista(bruto, "destaques", "destaques")):
        p = f"destaques[{i}]"
        d = v.item_tabela(d, p)
        destaques.append({"titulo": v.texto(d, "titulo", f"{p}.titulo", obrigatorio=True),
                          "texto": v.texto(d, "texto", f"{p}.texto"),
                          "imagem": v.imagem(d, "imagem", f"{p}.imagem")})

    galeria = v.imagens(bruto, "galeria", "galeria")

    categorias = []
    cardapio = v.tabela(bruto, "cardapio", "cardapio")
    for i, cat in enumerate(v.lista(cardapio, "categorias", "cardapio.categorias")):
        p = f"cardapio.categorias[{i}]"
        cat = v.item_tabela(cat, p)
        itens = []
        for j, it in enumerate(v.lista(cat, "itens", f"{p}.itens")):
            q = f"{p}.itens[{j}]"
            it = v.item_tabela(it, q)
            adicionais = []
            for a, ad in enumerate(v.lista(it, "adicionais", f"{q}.adicionais")):
                r = f"{q}.adicionais[{a}]"
                ad = v.item_tabela(ad, r)
                adicionais.append({"nome": v.texto(ad, "nome", f"{r}.nome", obrigatorio=True),
                                   "preco": v.numero(ad, "preco", f"{r}.preco", obrigatorio=True)})
            itens.append({"nome": v.texto(it, "nome", f"{q}.nome", obrigatorio=True),
                          "descricao": v.texto(it, "descricao", f"{q}.descricao"),
                          "preco": v.numero(it, "preco", f"{q}.preco", obrigatorio=True),
                          "imagem": v.imagem(it, "imagem", f"{q}.imagem"),
                          "selos": v.escolhas(it, "selos", f"{q}.selos", SELOS),
                          "adicionais": adicionais})
        categorias.append({"id": v.texto(cat, "id", f"{p}.id", obrigatorio=True),
                           "nome": v.texto(cat, "nome", f"{p}.nome", obrigatorio=True),
                           "descricao": v.texto(cat, "descricao", f"{p}.descricao"), "itens": itens})

    ev = v.tabela(bruto, "eventos", "eventos")
    lista = []
    for i, e in enumerate(v.lista(ev, "lista", "eventos.lista")):
        p = f"eventos.lista[{i}]"
        e = v.item_tabela(e, p)
        if ("data" in e) == ("em_dias" in e):
            raise v.erro(p, "informe exatamente um entre 'data' e 'em_dias'")
        evento = {"titulo": v.texto(e, "titulo", f"{p}.titulo", obrigatorio=True)}
        if "data" in e:
            d = e["data"]
            if isinstance(d, datetime.datetime) or not isinstance(d, datetime.date):
                raise v.erro(f"{p}.data", f"esperada data AAAA-MM-DD, recebido {d!r}")
            evento["data"] = d.isoformat()
        else:
            evento["em_dias"] = v.numero(e, "em_dias", f"{p}.em_dias", inteiro=True)
        for campo in ("hora", "atracao", "descricao", "valor"):
            evento[campo] = v.texto(e, campo, f"{p}.{campo}")
        evento["imagem"] = v.imagem(e, "imagem", f"{p}.imagem")
        lista.append(evento)

    fotos = []
    for i, f in enumerate(v.lista(bruto, "fotos", "fotos")):
        p = f"fotos[{i}]"
        f = v.item_tabela(f, p)
        fotos.append({n: v.texto(f, n, f"{p}.{n}", obrigatorio=(n == "arquivo"))
                      for n in ("arquivo", "url", "autor", "fonte")})

    return {
        "site": site, "contato": contato, "horarios": horarios, "capa": capa, "sobre": sobre,
        "destaques": destaques, "galeria": galeria, "cardapio": {"categorias": categorias},
        "eventos": {"vazio_mensagem": v.texto(ev, "vazio_mensagem", "eventos.vazio_mensagem"), "lista": lista},
        "fotos": fotos, "_pasta": pasta,
    }


def listar_sites(raiz: Path, temas_dir: Path | None = None) -> list[dict]:
    sites = [carregar_site(p.parent, temas_dir) for p in Path(raiz).glob("*/site.toml")]
    return sorted(sites, key=lambda s: (s["site"]["ordem"], s["site"]["slug"]))
