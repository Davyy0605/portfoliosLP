import pytest

from gerador.dados import ErroDeDados, avisos_config, carregar_config, carregar_site, listar_sites


def test_carrega_fixture_completa(site_dir, temas_dir):
    site = carregar_site(site_dir, temas_dir)
    assert site["site"]["slug"] == "completo"
    assert site["site"]["ordem"] == 99
    assert site["_pasta"] == site_dir
    assert site["eventos"]["lista"][1]["data"] == "2030-01-05"
    assert site["eventos"]["lista"][0]["em_dias"] == 3
    assert site["cardapio"]["categorias"][1]["itens"] == []
    assert site["cardapio"]["categorias"][0]["itens"][1]["selos"] == []


def test_padroes_site_minimo(site_dir, temas_dir):
    (site_dir / "site.toml").write_text(
        '[site]\nslug="completo"\ntema="teste"\nnome="X"\nsegmento="Bar"\n', encoding="utf-8")
    s = carregar_site(site_dir, temas_dir)
    assert s["site"]["modulos"] == [] and s["site"]["ordem"] == 99
    assert s["eventos"]["lista"] == [] and s["horarios"] == [] and s["fotos"] == []
    assert s["cardapio"]["categorias"] == [] and s["galeria"] == []


def test_erro_cita_arquivo_e_campo(site_dir, temas_dir, editar):
    editar("preco = 32.0", 'preco = "abc"')
    with pytest.raises(ErroDeDados, match=r"site\.toml: cardapio\.categorias\[0\]\.itens\[0\]\.preco"):
        carregar_site(site_dir, temas_dir)


def test_slug_diferente_da_pasta_falha(site_dir, temas_dir, editar):
    editar('slug = "completo"', 'slug = "outro"')
    with pytest.raises(ErroDeDados, match=r"site\.slug"):
        carregar_site(site_dir, temas_dir)


def test_tema_inexistente_falha(site_dir, temas_dir, editar):
    editar('tema = "teste"', 'tema = "nada"')
    with pytest.raises(ErroDeDados, match=r"site\.tema"):
        carregar_site(site_dir, temas_dir)


def test_imagem_inexistente_falha(site_dir, temas_dir, editar):
    editar('imagem = "capa.jpg"', 'imagem = "sumiu.jpg"')
    with pytest.raises(ErroDeDados, match=r"capa\.imagem.*sumiu\.jpg"):
        carregar_site(site_dir, temas_dir)


def test_evento_data_e_em_dias_juntos_falha(site_dir, temas_dir, editar):
    editar("em_dias = 3", "em_dias = 3\n  data = 2030-01-01")
    with pytest.raises(ErroDeDados, match=r"eventos\.lista\[0\]"):
        carregar_site(site_dir, temas_dir)


def test_evento_sem_data_nem_em_dias_falha(site_dir, temas_dir, editar):
    editar("em_dias = 3\n", "")
    with pytest.raises(ErroDeDados, match=r"eventos\.lista\[0\]"):
        carregar_site(site_dir, temas_dir)


def test_modulo_desconhecido_falha(site_dir, temas_dir, editar):
    editar('["eventos", "pedido"]', '["eventos", "voo"]')
    with pytest.raises(ErroDeDados, match=r"site\.modulos\[1\]"):
        carregar_site(site_dir, temas_dir)


def test_selo_desconhecido_falha(site_dir, temas_dir, editar):
    editar('["vegano", "novo"]', '["vegano", "magico"]')
    with pytest.raises(ErroDeDados, match=r"itens\[0\]\.selos\[1\]"):
        carregar_site(site_dir, temas_dir)


def test_campo_obrigatorio_ausente_falha(site_dir, temas_dir, editar):
    editar('nome = "Casa Completa"\n', "")
    with pytest.raises(ErroDeDados, match=r"site\.toml: site\.nome"):
        carregar_site(site_dir, temas_dir)


def test_toml_invalido_vira_erro_de_dados(site_dir, temas_dir):
    (site_dir / "site.toml").write_text("[site\nx=", encoding="utf-8")
    with pytest.raises(ErroDeDados, match=r"site\.toml"):
        carregar_site(site_dir, temas_dir)


def test_aviso_whatsapp_provisorio(tmp_path):
    c = tmp_path / "config.toml"
    c.write_text('url_base="https://x.app"\nwhatsapp="5500000000000"\n[marca]\nnome="D"\ncor="#7C3AED"\n')
    cfg = carregar_config(c)
    assert cfg["url_base"] == "https://x.app/"
    assert avisos_config(cfg) == ["config.toml: whatsapp ainda é o número provisório 5500000000000"]
    cfg["whatsapp"] = "5511987654321"
    assert avisos_config(cfg) == []


def test_whatsapp_invalido_falha(tmp_path):
    c = tmp_path / "config.toml"
    c.write_text('url_base="https://x.app/"\nwhatsapp="123"\n[marca]\nnome="D"\ncor="#7C3AED"\n')
    with pytest.raises(ErroDeDados, match=r"config\.toml: whatsapp"):
        carregar_config(c)


def test_listar_sites_ordena_por_ordem(tmp_path, temas_dir):
    base = '[site]\nslug="{s}"\ntema="teste"\nnome="X"\nsegmento="Bar"\n{o}'
    for slug, ordem in [("b", "ordem=1\n"), ("a", "ordem=2\n"), ("c", "ordem=1\n"), ("z", "")]:
        (tmp_path / "sites" / slug).mkdir(parents=True)
        (tmp_path / "sites" / slug / "site.toml").write_text(base.format(s=slug, o=ordem))
    sites = listar_sites(tmp_path / "sites", temas_dir)
    assert [s["site"]["slug"] for s in sites] == ["b", "c", "a", "z"]


def test_whatsapp_config_e_contato_normalizados(tmp_path, site_dir, temas_dir, editar):
    c = tmp_path / "config.toml"
    c.write_text('url_base="https://x.app/"\nwhatsapp="(11) 98765-4321"\n[marca]\nnome="D"\ncor="#7C3AED"\n')
    assert carregar_config(c)["whatsapp"] == "5511987654321"
    editar('whatsapp = ""', 'whatsapp = "11 98765-4321"')
    assert carregar_site(site_dir, temas_dir)["contato"]["whatsapp"] == "5511987654321"
    editar('whatsapp = "11 98765-4321"', 'whatsapp = "12"')
    with pytest.raises(ErroDeDados, match=r"site\.toml: contato\.whatsapp"):
        carregar_site(site_dir, temas_dir)


def test_arquivo_ilegivel_vira_erro_de_dados(site_dir, temas_dir):
    (site_dir / "site.toml").write_bytes(b'[site]\nnome = "\xff\xfe"\n')
    with pytest.raises(ErroDeDados, match=r"site\.toml"):
        carregar_site(site_dir, temas_dir)
    (site_dir / "site.toml").unlink()
    (site_dir / "site.toml").mkdir()
    with pytest.raises(ErroDeDados, match=r"site\.toml"):
        carregar_site(site_dir, temas_dir)


@pytest.mark.parametrize("valor", ["nan", "inf"])
def test_preco_nan_inf_falha(site_dir, temas_dir, editar, valor):
    editar("preco = 32.0", f"preco = {valor}")
    with pytest.raises(ErroDeDados, match=r"site\.toml: cardapio\.categorias\[0\]\.itens\[0\]\.preco"):
        carregar_site(site_dir, temas_dir)


@pytest.mark.parametrize("antigo,novo,campo", [
    ('id = "drinks"', 'id = "Dri nks"', r"cardapio\.categorias\[0\]\.id"),
    ('cor = "#112233"', 'cor = "roxo"', r"site\.cor"),
    ('slug = "completo"', 'slug = "hub"', r"site\.slug"),
    ('arquivo = "capa.jpg"', 'arquivo = "../capa.jpg"', r"fotos\[0\]\.arquivo"),
    ('imagem = "capa.jpg"', 'imagem = "x/capa.jpg"', r"capa\.imagem"),
    ('mapa_url = "https://www.google.com/maps/embed?pb=x"', 'mapa_url = "http://x"', r"contato\.mapa_url"),
])
def test_validacoes_de_formato(site_dir, temas_dir, editar, antigo, novo, campo):
    editar(antigo, novo)
    with pytest.raises(ErroDeDados, match=campo):
        carregar_site(site_dir, temas_dir)


def test_categoria_id_repetido(site_dir, temas_dir):
    arq = site_dir / "site.toml"
    arq.write_text(arq.read_text(encoding="utf-8") + '\n[[cardapio.categorias]]\nid = "drinks"\nnome = "Outra"\n', encoding="utf-8")
    with pytest.raises(ErroDeDados, match=r"categorias\[\d+\]\.id.*repetido"):
        carregar_site(site_dir, temas_dir)


def test_mesmo_stem_de_imagem(site_dir, temas_dir):
    from PIL import Image
    Image.new("RGB", (8, 8)).save(site_dir / "imagens" / "capa.png")
    with pytest.raises(ErroDeDados, match=r"capa\.jpg.*capa\.png"):
        carregar_site(site_dir, temas_dir)


@pytest.mark.parametrize("entrada", ["@usuario", "usuario", "instagram.com/usuario", "https://www.instagram.com/usuario/"])
def test_instagram_normalizado(site_dir, temas_dir, editar, entrada):
    editar('instagram = "@completo"', f'instagram = "{entrada}"')
    assert carregar_site(site_dir, temas_dir)["contato"]["instagram"] == "usuario"


def test_aviso_url_base_provisoria(tmp_path):
    c = tmp_path / "config.toml"
    c.write_text('url_base="https://davy.netlify.app/"\nwhatsapp="5511987654321"\n[marca]\nnome="D"\ncor="#7C3AED"\n')
    (aviso,) = avisos_config(carregar_config(c))
    assert "url_base" in aviso and "QR" in aviso and "Netlify" in aviso


def test_cor_da_marca_invalida(tmp_path):
    c = tmp_path / "config.toml"
    c.write_text('url_base="https://x.app/"\nwhatsapp="5511987654321"\n[marca]\nnome="D"\ncor="roxo"\n')
    with pytest.raises(ErroDeDados, match=r"marca\.cor"):
        carregar_config(c)
