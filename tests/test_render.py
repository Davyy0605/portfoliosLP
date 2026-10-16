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
