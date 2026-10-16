"""Comportamento dos módulos JS no navegador real (Playwright + chromium)."""
import sys
import urllib.parse
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "ferramentas"))
from capturar import servir  # noqa: E402

from gerador.dados import carregar_config, carregar_site  # noqa: E402
from gerador.render import copiar_estaticos, criar_ambiente, render_site  # noqa: E402

sync_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def navegador():
    with sync_api.sync_playwright() as p:
        try:
            nav = p.chromium.launch()
        except Exception as e:  # chromium não instalado
            pytest.skip(f"chromium do Playwright indisponível: {e}")
        yield nav
        nav.close()


@pytest.fixture
def pagina(navegador):
    p = navegador.new_page()
    p.set_default_timeout(60000)  # máquina de CI/dev pode estar carregada
    yield p
    p.close()


@pytest.fixture
def abrir(raiz, pagina):
    """abrir(caminho): gera o site da fixture, serve e abre a página."""
    pilha = []

    def _abrir(caminho):
        env = criar_ambiente(raiz)
        site = carregar_site(raiz / "sites" / "completo", raiz / "temas")
        out = raiz / "out"
        render_site(env, site, carregar_config(raiz / "config.toml"), out, "")
        copiar_estaticos(raiz, out)
        ctx = servir(out)
        pilha.append(ctx)
        pagina.goto(ctx.__enter__() + caminho)
        return pagina

    yield _abrir
    for ctx in pilha:
        ctx.__exit__(None, None, None)


def test_busca_filtra_itens_categorias_e_abas(abrir):
    p = abrir("cardapio/")
    p.fill("input[data-busca]", "gin")
    assert p.locator("[data-item]", has_text="Água").is_hidden()
    assert p.locator("[data-item]", has_text="Gin").is_visible()
    assert p.locator("section#porcoes").is_hidden()
    assert p.locator("nav[data-abas] a[href='#porcoes']").is_hidden()
    assert p.locator("nav[data-abas] a[href='#drinks']").is_visible()
    assert p.locator("[data-sem-resultado]").is_hidden()


def test_busca_sem_resultado(abrir):
    p = abrir("cardapio/")
    p.fill("input[data-busca]", "xyzzy")
    assert p.locator("[data-sem-resultado]").is_visible()
    assert p.locator("[data-item]:visible").count() == 0


def test_eventos_futuro_formatado_e_vazio_oculto(abrir):
    p = abrir("")
    assert p.locator("[data-eventos-vazio]").is_hidden()
    samba = p.locator("[data-evento]", has_text="Samba")
    assert samba.locator("[data-evento-data]").inner_text() not in ("", "Em breve")
    assert "jan" in p.locator("[data-evento]", has_text="Jazz").locator("[data-evento-data]").inner_text().lower()


def test_eventos_todos_passados_mostra_mensagem(raiz, editar, abrir):
    editar("em_dias = 3", "data = 2020-01-01")
    editar("data = 2030-01-05", "data = 2020-02-02")
    p = abrir("")
    assert p.locator("[data-evento]:visible").count() == 0
    assert p.locator("[data-eventos-vazio]").is_visible()
    assert "Novas atrações em breve." in p.locator("[data-eventos-vazio]").inner_text()


def test_carrinho(abrir):
    p = abrir("cardapio/")
    p.click("[data-carrinho-abrir]")
    enviar = p.locator("a[data-carrinho-enviar]")
    assert enviar.get_attribute("aria-disabled") == "true" and enviar.get_attribute("href") is None
    p.keyboard.press("Escape")

    p.click("button[data-adicionar][data-nome='Gin']")
    p.click("button[data-adicionar][data-nome='Água']")
    p.click("[data-carrinho-abrir]")
    assert p.locator("[data-carrinho-total]").inner_text() == "R$ 37,00"
    href = enviar.get_attribute("href")
    assert href.startswith("https://wa.me/")
    msg = urllib.parse.unquote(href.split("?text=", 1)[1])
    assert "Gin" in msg and "Água" in msg and "R$ 37,00" in msg

    # o foco permanece num botão do dialog após apertar "+"
    p.locator("dialog[data-carrinho] button[data-acao='mais']").first.click()
    assert p.evaluate("document.activeElement.closest('dialog') !== null && document.activeElement.tagName === 'BUTTON'")

    p.reload()
    p.click("[data-carrinho-abrir]")
    assert p.locator("[data-carrinho-lista] li").count() == 2
    assert p.locator("[data-carrinho-total]").inner_text() == "R$ 69,00"
