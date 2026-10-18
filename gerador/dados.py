"""Leitura e validação de config.toml e site.toml."""
import datetime
import math
import re
import tomllib
from pathlib import Path

from gerador.formatos import NUMERO_PROVISORIO as PROVISORIO, normalizar_whatsapp

MODULOS = {"eventos", "pedido"}
SELOS = {"vegano", "vegetariano", "sem-gluten", "picante", "novo", "chef"}
CTAS = {"cardapio", "reservar", "pedir", "agendar"}
RAMOS = {"gastronomia", "beleza"}
DIAS = ["dom", "seg", "ter", "qua", "qui", "sex", "sab"]
PORTES = ["P", "M", "G"]
RE_PERIODO = re.compile(r"(\d{2}):(\d{2})-(\d{2}):(\d{2})")
RE_ID = re.compile(r"[a-z0-9-]+")
RE_COR = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")
RE_INSTAGRAM = re.compile(r"(?:https?://)?(?:www\.)?(?:instagram\.com/)?@?([A-Za-z0-9._]+)/?(?:\?.*)?")
URL_PROVISORIA = "https://davy.netlify.app/"
SLUGS_RESERVADOS = {"static", "img", "hub", "gastronomia", "beleza"}
EXT_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}


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
        if isinstance(v, bool) or not isinstance(v, tipos) or v < 0 or (isinstance(v, float) and not math.isfinite(v)):
            raise self.erro(caminho, f"esperado número{' inteiro' if inteiro else ''} não negativo, recebido {v!r}")
        return v

    def whatsapp(self, valor, caminho):
        try:
            return normalizar_whatsapp(valor)
        except ValueError as e:
            raise self.erro(caminho, str(e)) from None

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

    def nome_arquivo(self, nome, caminho):
        if nome in (".", "..") or "/" in nome or "\\" in nome or Path(nome).name != nome:
            raise self.erro(caminho, f"nome de arquivo {nome!r} não pode conter caminho")

    def cor(self, valor, caminho):
        if valor and not RE_COR.fullmatch(valor):
            raise self.erro(caminho, f"cor {valor!r} inválida; use #rrggbb")
        return valor

    def arquivo_imagem(self, nome, caminho):
        if nome:
            self.nome_arquivo(nome, caminho)
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
    except UnicodeDecodeError:
        raise ErroDeDados(f"{rotulo}: arquivo não está em UTF-8 válido") from None
    except OSError as e:
        raise ErroDeDados(f"{rotulo}: não foi possível ler o arquivo ({e.strerror or e})") from None


def carregar_config(caminho: Path) -> dict:
    v = _V("config.toml")
    bruto = _ler(caminho, "config.toml")
    marca = v.tabela(bruto, "marca", "marca")
    zap = v.texto(bruto, "whatsapp", "whatsapp", obrigatorio=True)
    digitos = v.whatsapp(zap, "whatsapp")
    url = v.texto(bruto, "url_base", "url_base", obrigatorio=True)
    nome_marca = v.texto(marca, "nome", "marca.nome", obrigatorio=True)
    return {
        "marca": {
            "nome": nome_marca,
            "cor": v.cor(v.texto(marca, "cor", "marca.cor", obrigatorio=True), "marca.cor"),
        },
        "whatsapp": digitos,
        "url_base": url if url.endswith("/") else url + "/",
        "ramos": _ramos(v, bruto, nome_marca),
    }


def _ramos(v: _V, bruto: dict, marca: str) -> dict:
    """[ramos.*] na ordem do arquivo; sem a tabela, só gastronomia com os textos antigos do hub."""
    if "ramos" not in bruto:
        return {"gastronomia": {
            "nome": "Bares e restaurantes",
            "resumo": "Cardápio digital com QR na mesa",
            "titulo": "Cardápios digitais e sites para bares e restaurantes.",
            "mensagem": f"Olá, {marca}! Vi o portfólio e quero um site para o meu estabelecimento.",
        }}
    ramos = {}
    for ramo, d in v.tabela(bruto, "ramos", "ramos").items():
        if ramo not in RAMOS:
            raise v.erro(f"ramos.{ramo}", f"ramo desconhecido; use um de {sorted(RAMOS)}")
        d = v.item_tabela(d, f"ramos.{ramo}")
        ramos[ramo] = {k: v.texto(d, k, f"ramos.{ramo}.{k}", obrigatorio=True)
                       for k in ("nome", "resumo", "titulo", "mensagem")}
    return ramos


def avisos_config(config: dict) -> list[str]:
    avisos = []
    if config["whatsapp"] == PROVISORIO:
        avisos.append(f"config.toml: whatsapp ainda é o número provisório {PROVISORIO}")
    if config["url_base"] == URL_PROVISORIA:
        avisos.append(f"config.toml: url_base ainda é {URL_PROVISORIA}; os QR codes vão apontar para esse endereço. "
                      "Troque pelo endereço real do Netlify")
    return avisos


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
    if not RE_ID.fullmatch(slug) or slug in SLUGS_RESERVADOS:
        raise v.erro("site.slug", f"{slug!r} inválido; use letras minúsculas, números e hífen (não use {sorted(SLUGS_RESERVADOS)})")
    if slug != pasta.name:
        raise v.erro("site.slug", f"{slug!r} deve ser igual ao nome da pasta {pasta.name!r}")
    tema = v.texto(s, "tema", "site.tema", obrigatorio=True)
    if not (Path(temas_dir) / tema).is_dir():
        raise v.erro("site.tema", f"tema {tema!r} não existe em temas/")
    ramo = v.texto(s, "ramo", "site.ramo", "gastronomia")
    if ramo not in RAMOS:
        raise v.erro("site.ramo", f"{ramo!r} inválido; use um de {sorted(RAMOS)}")
    site = {
        "ramo": ramo, "slug": slug, "tema": tema,
        "nome": v.texto(s, "nome", "site.nome", obrigatorio=True),
        "segmento": v.texto(s, "segmento", "site.segmento", obrigatorio=True),
        "ordem": v.numero(s, "ordem", "site.ordem", 99, inteiro=True),
        "slogan": v.texto(s, "slogan", "site.slogan"),
        "descricao": v.texto(s, "descricao", "site.descricao"),
        "modulos": v.escolhas(s, "modulos", "site.modulos", MODULOS),
        "cor": v.cor(v.texto(s, "cor", "site.cor"), "site.cor"),
    }

    c = v.tabela(bruto, "contato", "contato")
    contato = {k: v.texto(c, k, f"contato.{k}") for k in
               ("whatsapp", "telefone", "instagram", "endereco", "mapa_url")}
    if contato["instagram"].strip():
        m = RE_INSTAGRAM.fullmatch(contato["instagram"].strip())
        if not m:
            raise v.erro("contato.instagram", f"{contato['instagram']!r} não parece um perfil do Instagram")
        contato["instagram"] = m.group(1)
    if contato["mapa_url"] and not contato["mapa_url"].startswith("https://"):
        raise v.erro("contato.mapa_url", "deve começar com https://")
    if contato["whatsapp"]:
        contato["whatsapp"] = v.whatsapp(contato["whatsapp"], "contato.whatsapp")

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

    if v.pasta_imagens is not None and v.pasta_imagens.is_dir():
        vistos = {}
        for f in sorted(v.pasta_imagens.iterdir()):
            if f.suffix.lower() in EXT_IMAGEM:
                if f.stem in vistos:
                    raise v.erro("imagens/", f"{vistos[f.stem]!r} e {f.name!r} têm o mesmo nome base e gerariam o mesmo .webp")
                vistos[f.stem] = f.name

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
        cid = v.texto(cat, "id", f"{p}.id", obrigatorio=True)
        if not RE_ID.fullmatch(cid):
            raise v.erro(f"{p}.id", f"{cid!r} inválido; use letras minúsculas, números e hífen")
        if any(c["id"] == cid for c in categorias):
            raise v.erro(f"{p}.id", f"id {cid!r} repetido")
        categorias.append({"id": cid,
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
        foto = {n: v.texto(f, n, f"{p}.{n}", obrigatorio=(n == "arquivo"))
                for n in ("arquivo", "url", "autor", "fonte")}
        v.nome_arquivo(foto["arquivo"], f"{p}.arquivo")
        fotos.append(foto)

    return {
        **_beleza(v, bruto, ramo == "beleza"),
        "site": site, "contato": contato, "horarios": horarios, "capa": capa, "sobre": sobre,
        "destaques": destaques, "galeria": galeria, "cardapio": {"categorias": categorias},
        "eventos": {"vazio_mensagem": v.texto(ev, "vazio_mensagem", "eventos.vazio_mensagem"), "lista": lista},
        "fotos": fotos, "_pasta": pasta,
    }


def _funcionamento(v, lista, caminho):
    """Converte [[...funcionamento]] em {dia: [[ini, fim], ...]} (minutos desde 00:00)."""
    res = {}
    for i, f in enumerate(lista):
        p = f"{caminho}[{i}]"
        f = v.item_tabela(f, p)
        dias = v.escolhas(f, "dias", f"{p}.dias", set(DIAS))
        if not dias:
            raise v.erro(f"{p}.dias", "informe ao menos um dia")
        brutos = v.lista(f, "periodos", f"{p}.periodos", obrigatorio=True)
        if not brutos:
            raise v.erro(f"{p}.periodos", "informe ao menos um período")
        periodos = []
        for j, per in enumerate(brutos):
            q = f"{p}.periodos[{j}]"
            m = RE_PERIODO.fullmatch(per) if isinstance(per, str) else None
            if not m:
                raise v.erro(q, f"{per!r} inválido; use HH:MM-HH:MM")
            ini, fim = int(m[1]) * 60 + int(m[2]), int(m[3]) * 60 + int(m[4])
            if int(m[2]) > 59 or int(m[4]) > 59 or fim > 1440 or ini >= fim:
                raise v.erro(q, f"{per!r} inválido; o início deve ser anterior ao fim, em horas válidas")
            periodos.append([ini, fim])
        for d in dias:
            ordenados = sorted(res.get(d, []) + periodos)
            for a, b in zip(ordenados, ordenados[1:]):
                if b[0] < a[1]:
                    raise v.erro(f"{p}.periodos", f"períodos com sobreposição em {d!r}")
            res[d] = ordenados
    return res


def _faixa(v, d, chave, caminho, padrao, minimo, maximo):
    n = v.numero(d, chave, caminho, padrao, inteiro=True)
    if not minimo <= n <= maximo:
        raise v.erro(caminho, f"deve estar entre {minimo} e {maximo}, recebido {n}")
    return n


def _booleano(v, d, chave, caminho):
    b = d.get(chave, False)
    if not isinstance(b, bool):
        raise v.erro(caminho, f"esperado verdadeiro/falso, recebido {b!r}")
    return b


def _id_unico(v, d, anteriores, caminho):
    i = v.texto(d, "id", f"{caminho}.id", obrigatorio=True)
    if not RE_ID.fullmatch(i):
        raise v.erro(f"{caminho}.id", f"{i!r} inválido; use letras minúsculas, números e hífen")
    if any(x["id"] == i for x in anteriores):
        raise v.erro(f"{caminho}.id", f"id {i!r} repetido")
    return i


def _beleza(v, bruto, exigir):
    """Serviços, equipe e agenda; obrigatórios só no ramo beleza, vazios nos demais."""
    ag = v.tabela(bruto, "agenda", "agenda")
    pede_pet = _booleano(v, ag, "pede_pet", "agenda.pede_pet")
    agenda = {"intervalo": _faixa(v, ag, "intervalo", "agenda.intervalo", 30, 5, 240),
              "dias": _faixa(v, ag, "dias", "agenda.dias", 14, 1, 60),
              "pede_pet": pede_pet,
              "funcionamento": _funcionamento(v, v.lista(ag, "funcionamento", "agenda.funcionamento"),
                                              "agenda.funcionamento")}
    if exigir and not agenda["funcionamento"]:
        raise v.erro("agenda.funcionamento", "obrigatório (ao menos 1) no ramo beleza")

    servicos = []
    for i, sv in enumerate(v.lista(bruto, "servicos", "servicos")):
        p = f"servicos[{i}]"
        sv = v.item_tabela(sv, p)
        sid = _id_unico(v, sv, servicos, p)
        duracao = v.numero(sv, "duracao", f"{p}.duracao", obrigatorio=True, inteiro=True)
        if duracao <= 0:
            raise v.erro(f"{p}.duracao", "deve ser maior que zero")
        porte = None
        if "porte" in sv:
            if not pede_pet:
                raise v.erro(f"{p}.porte", "exige agenda.pede_pet = true")
            bp = v.tabela(sv, "porte", f"{p}.porte")
            if not bp or any(k not in PORTES for k in bp):
                raise v.erro(f"{p}.porte", f"use chaves entre {PORTES}")
            porte = {k: v.numero(bp, k, f"{p}.porte.{k}", obrigatorio=True) for k in bp}
        elif "preco" not in sv:
            raise v.erro(f"{p}.preco", "campo obrigatório ausente (ou informe porte)")
        servicos.append({"id": sid, "nome": v.texto(sv, "nome", f"{p}.nome", obrigatorio=True),
                         "categoria": v.texto(sv, "categoria", f"{p}.categoria"),
                         "descricao": v.texto(sv, "descricao", f"{p}.descricao"),
                         "duracao": duracao, "preco": v.numero(sv, "preco", f"{p}.preco"),
                         "a_partir_de": _booleano(v, sv, "a_partir_de", f"{p}.a_partir_de"),
                         "porte": porte})
    if exigir and not servicos:
        raise v.erro("servicos", "obrigatório (ao menos 1) no ramo beleza")

    adicionais = []
    for i, ad in enumerate(v.lista(bruto, "adicionais", "adicionais")):
        p = f"adicionais[{i}]"
        ad = v.item_tabela(ad, p)
        adicionais.append({"id": _id_unico(v, ad, adicionais, p),
                           "nome": v.texto(ad, "nome", f"{p}.nome", obrigatorio=True),
                           "preco": v.numero(ad, "preco", f"{p}.preco"),
                           "pede_bairro": _booleano(v, ad, "pede_bairro", f"{p}.pede_bairro")})

    ids = {x["id"] for x in servicos}
    equipe = []
    for i, e in enumerate(v.lista(bruto, "equipe", "equipe")):
        p = f"equipe[{i}]"
        e = v.item_tabela(e, p)
        svs = v.lista(e, "servicos", f"{p}.servicos")
        for j, x in enumerate(svs):
            if x not in ids:
                raise v.erro(f"{p}.servicos[{j}]", f"serviço {x!r} não existe em [[servicos]]")
        func = _funcionamento(v, v.lista(e, "funcionamento", f"{p}.funcionamento"), f"{p}.funcionamento")
        equipe.append({"nome": v.texto(e, "nome", f"{p}.nome", obrigatorio=True),
                       "especialidade": v.texto(e, "especialidade", f"{p}.especialidade"),
                       "foto": v.imagem(e, "foto", f"{p}.foto"),
                       "servicos": svs, "funcionamento": func or None})

    depoimentos = []
    for i, d in enumerate(v.lista(bruto, "depoimentos", "depoimentos")):
        p = f"depoimentos[{i}]"
        d = v.item_tabela(d, p)
        depoimentos.append({"nome": v.texto(d, "nome", f"{p}.nome", obrigatorio=True),
                            "texto": v.texto(d, "texto", f"{p}.texto", obrigatorio=True),
                            "servico": v.texto(d, "servico", f"{p}.servico")})
    perguntas = []
    for i, q in enumerate(v.lista(bruto, "perguntas", "perguntas")):
        p = f"perguntas[{i}]"
        q = v.item_tabela(q, p)
        perguntas.append({"pergunta": v.texto(q, "pergunta", f"{p}.pergunta", obrigatorio=True),
                          "resposta": v.texto(q, "resposta", f"{p}.resposta", obrigatorio=True)})
    return {"agenda": agenda, "servicos": servicos, "adicionais": adicionais, "equipe": equipe,
            "depoimentos": depoimentos, "perguntas": perguntas}


def listar_sites(raiz: Path, temas_dir: Path | None = None) -> list[dict]:
    sites = [carregar_site(p.parent, temas_dir) for p in Path(raiz).glob("*/site.toml")]
    return sorted(sites, key=lambda s: (s["site"]["ordem"], s["site"]["slug"]))
