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


@pytest.fixture
def abrir_beleza(raiz_beleza, pagina):
    """abrir_beleza(caminho): gera o site de beleza da fixture, serve e abre a página."""
    pilha = []

    def _abrir(caminho):
        env = criar_ambiente(raiz_beleza)
        site = carregar_site(raiz_beleza / "sites" / "studio-teste", raiz_beleza / "temas")
        out = raiz_beleza / "out"
        render_site(env, site, carregar_config(raiz_beleza / "config.toml"), out, "")
        copiar_estaticos(raiz_beleza, out)
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


def test_carrinho_aviso_e_barra(abrir):
    p = abrir("cardapio/")
    assert p.locator("[data-barra]").is_hidden()
    p.click("button[data-adicionar][data-nome='Gin']")
    assert p.locator("[data-aviso]").inner_text() == "✓ Adicionado: Gin"
    barra = p.locator("[data-barra]")
    assert barra.is_visible()
    assert barra.locator("[data-barra-etiquetas] li").all_inner_texts() == ["Gin"]
    assert "1 item" in barra.locator("[data-barra-linha]").inner_text()
    assert p.locator("button[data-adicionar][data-nome='Gin'][data-escolhido]").count() == 1
    barra.click()
    assert p.locator("dialog[data-carrinho]").is_visible()


def test_carrinho(abrir):
    p = abrir("cardapio/")
    assert p.locator("[data-barra]").is_hidden()
    enviar = p.locator("a[data-carrinho-enviar]")
    assert enviar.get_attribute("aria-disabled") == "true" and enviar.get_attribute("href") is None

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


def test_agendamento_fluxo_completo(abrir_beleza):
    p = abrir_beleza("agendar/")
    p.check("input[data-servico-id='corte']")
    assert p.locator("[data-aviso]").inner_text() == "✓ Adicionado: Corte masculino"
    p.check("input[data-servico-id='barba']")
    assert p.locator("[data-barra-etiquetas] li").all_inner_texts() == ["Corte masculino", "Barba completa"]
    p.click("[data-barra]")  # -> profissional
    assert p.locator("[data-passo='profissional'] input[type=radio]").count() == 3  # sem preferência, Rafael, Ana
    p.check("[data-passo='profissional'] input[value='']")
    p.click("[data-barra]")  # -> quando
    p.locator("[data-passo='quando'] input[name=dia]:not([disabled])").first.check()
    p.locator("[data-passo='quando'] input[name=hora]").first.check()
    p.click("[data-barra]")  # -> dados
    p.fill("input[name=nome]", "Lucas")
    msg = urllib.parse.unquote(p.locator("a[data-agendar-enviar]").get_attribute("href").split("?text=", 1)[1])
    assert "• Corte masculino (R$ 45,00)" in msg and "Profissional: sem preferência" in msg and "Nome: Lucas" in msg


def test_agendamento_troca_servico_limpa_profissional(abrir_beleza):
    p = abrir_beleza("agendar/")
    p.check("input[data-servico-id='corte']")
    p.click("[data-barra]")
    p.check("[data-passo='profissional'] input[type=radio] >> nth=2")  # Thiago (Rafael, Thiago, Ana? ordem da equipe)
    assert p.locator("[data-passo='profissional'] input[type=radio]:checked").count() == 1
    nome = p.locator("[data-passo='profissional'] input[type=radio]:checked").get_attribute("data-nome")
    assert nome == "Thiago"
    p.click("[data-passo-voltar]:visible")  # volta aos serviços
    p.check("input[data-servico-id='barba']")
    p.click("[data-barra]")
    assert p.locator("[data-passo='profissional'] input[data-nome='Thiago']").count() == 0
    assert p.locator("[data-passo='profissional'] input[value='']").is_checked()


def test_agendamento_envio_bloqueado_sem_nome(abrir_beleza):
    p = abrir_beleza("agendar/")
    p.check("input[data-servico-id='corte']")
    p.click("[data-barra]")
    p.check("[data-passo='profissional'] input[value='']")
    p.click("[data-barra]")
    p.locator("[data-passo='quando'] input[name=dia]:not([disabled])").first.check()
    p.locator("[data-passo='quando'] input[name=hora]").first.check()
    p.click("[data-barra]")
    enviar = p.locator("a[data-agendar-enviar]")
    assert enviar.get_attribute("aria-disabled") == "true"
    assert enviar.get_attribute("href") is None
