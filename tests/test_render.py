from gerador.dados import carregar_config, carregar_site
from gerador.render import copiar_estaticos, criar_ambiente, render_hub, render_site


def _gerar(raiz, editar=None):
    env = criar_ambiente(raiz)
    config = carregar_config(raiz / "config.toml")
    site = carregar_site(raiz / "sites" / "completo", raiz / "temas")
    out = raiz / "out"
    render_site(env, site, config, out, "")
    return env, config, site, out


def test_render_site(raiz, editar):
    editar("preco = 32.0", "preco = 42.9")
    _, _, _, out = _gerar(raiz)
    landing = (out / "index.html").read_text(encoding="utf-8")
    cardapio = (out / "cardapio" / "index.html").read_text(encoding="utf-8")
    assert "Casa Completa" in landing and "Casa Completa" in cardapio
    assert "R$ 42,90" in cardapio
    assert 'href="static/css/base.css"' in landing and 'href="tema.css"' in landing
    assert 'href="../static/css/base.css"' in cardapio and 'href="../tema.css"' in cardapio
    assert 'content="#112233"' in landing
    assert (out / "tema.css").is_file() and (out / "img").is_dir() and (out / "cardapio" / "img").is_dir()


def test_html_escapado(raiz, editar):
    editar('nome = "Gin"', 'nome = "<script>alert(1)</script> & \\"x\\""')
    _, _, _, out = _gerar(raiz)
    html = (out / "cardapio" / "index.html").read_text(encoding="utf-8")
    assert "&lt;script&gt;" in html and "<script>alert" not in html


def test_hub_e_estaticos(raiz, tmp_path):
    env = criar_ambiente(raiz)
    config = carregar_config(raiz / "config.toml")
    site = carregar_site(raiz / "sites" / "completo", raiz / "temas")
    out = tmp_path / "hub"
    render_hub(env, [site], config, out)
    copiar_estaticos(raiz, out)
    html = (out / "index.html").read_text(encoding="utf-8")
    assert "Casa Completa" in html and 'href="completo/"' in html and "<svg" in html
    assert (out / "img" / "completo" / "capa-8.webp").is_file()
    assert (out / "static").is_dir()


def _html(raiz, pagina="cardapio"):
    _, _, _, out = _gerar(raiz)
    return ((out / "cardapio" / "index.html") if pagina == "cardapio" else (out / "index.html")).read_text(encoding="utf-8")


def test_cardapio_item_sem_imagem_e_categoria_vazia(raiz):
    html = _html(raiz)
    agua = html[html.index("Água"):html.index("Batata")]
    assert "<img" not in agua
    assert 'href="#vazia"' not in html and 'id="vazia"' not in html
    assert 'href="#drinks"' in html and 'id="porcoes"' in html


def test_cardapio_um_aviso_e_centavos(raiz, editar):
    editar("preco = 32.0", "preco = 42.9")
    html = _html(raiz)
    assert html.count("data-sem-resultado") == 1
    assert 'data-centavos="4290"' in html
    assert "data-adicionar" in html and 'aria-label="Vegano"' in html


def test_cardapio_sem_pedido_nao_tem_botao_nem_dialog(raiz, editar):
    editar('modulos = ["eventos", "pedido"]', 'modulos = ["eventos"]')
    html = _html(raiz)
    assert "<dialog data-carrinho" not in html and "data-adicionar" not in html


def test_cardapio_com_pedido_tem_dialog(raiz):
    assert "<dialog data-carrinho" in _html(raiz)


def test_eventos_data_e_em_dias(raiz):
    html = _html(raiz, "landing")
    assert 'data-em-dias="3"' in html and 'data-data="2030-01-05"' in html
    assert "data-eventos-vazio" in html and "Novas atrações em breve." in html
    assert "https://wa.me/" in html and "Quero%20reservar%20para%20Samba%20%28Trio%29." in html


def test_rodape_creditos_e_demo(raiz):
    html = _html(raiz, "landing")
    assert "Fulano" in html and "Site de demonstração por Davy" in html


def test_hub_otimiza_so_a_capa(raiz, tmp_path):
    env = criar_ambiente(raiz)
    config = carregar_config(raiz / "config.toml")
    site = carregar_site(raiz / "sites" / "completo", raiz / "temas")
    out = tmp_path / "hub"
    render_hub(env, [site], config, out, tmp_path / "cache")
    nomes = [p.name for p in (out / "img" / "completo").iterdir()]
    assert nomes and all(n.startswith("capa-") for n in nomes)
    assert (tmp_path / "cache" / "hub" / "sites" / "completo").is_dir()


def test_cache_separado_por_pasta_de_origem(raiz, tmp_path):
    import shutil
    from PIL import Image
    env = criar_ambiente(raiz)
    config = carregar_config(raiz / "config.toml")
    demo = carregar_site(raiz / "sites" / "completo", raiz / "temas")
    (raiz / "clientes").mkdir(exist_ok=True)
    shutil.copytree(raiz / "sites" / "completo", raiz / "clientes" / "completo")
    Image.new("RGB", (8, 8), "blue").save(raiz / "clientes" / "completo" / "imagens" / "capa.jpg")
    cli = carregar_site(raiz / "clientes" / "completo", raiz / "temas")
    cache = tmp_path / "cache"
    render_site(env, demo, config, tmp_path / "a", "", "", cache)
    render_site(env, cli, config, tmp_path / "b", "", "", cache)
    assert (cache / "sites" / "completo").is_dir() and (cache / "clientes" / "completo").is_dir()
    a = Image.open(tmp_path / "a" / "img" / "capa-8.webp").convert("RGB").getpixel((0, 0))
    b = Image.open(tmp_path / "b" / "img" / "capa-8.webp").convert("RGB").getpixel((0, 0))
    assert a[0] > 200 and b[2] > 200
