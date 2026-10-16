import build


def test_portfolio(raiz, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(build, "RAIZ", raiz)
    saida = tmp_path / "dist"
    assert build.main(["--saida", str(saida)]) == 0
    assert (saida / "index.html").is_file()
    assert (saida / "completo" / "index.html").is_file()
    assert (saida / "completo" / "cardapio" / "index.html").is_file()
    assert "AVISO:" in capsys.readouterr().out  # whatsapp provisório


def test_cliente(raiz, tmp_path, monkeypatch):
    monkeypatch.setattr(build, "RAIZ", raiz)
    saida = tmp_path / "dist"
    assert build.main(["--site", "completo", "--saida", str(saida)]) == 0
    assert (saida / "index.html").is_file() and (saida / "cardapio" / "index.html").is_file()
    assert not (saida / "completo").exists()


def test_sem_sites(raiz, tmp_path, monkeypatch):
    monkeypatch.setattr(build, "RAIZ", raiz)
    import shutil
    shutil.rmtree(raiz / "sites")
    assert build.main(["--saida", str(tmp_path / "d")]) == 0


def test_erro_sem_traceback(raiz, tmp_path, monkeypatch, capsys, editar):
    monkeypatch.setattr(build, "RAIZ", raiz)
    editar("preco = 5", 'preco = "cinco"')
    assert build.main(["--saida", str(tmp_path / "d")]) == 1
    err = capsys.readouterr().err
    assert "preco" in err and "Traceback" not in err


def _html(p):
    return p.read_text(encoding="utf-8")


def test_caminhos_portfolio_e_og(raiz, tmp_path, monkeypatch):
    monkeypatch.setattr(build, "RAIZ", raiz)
    d = tmp_path / "dist"
    assert build.main(["--saida", str(d)]) == 0
    land, card = _html(d / "completo" / "index.html"), _html(d / "completo" / "cardapio" / "index.html")
    assert 'href="../static/css/base.css"' in land and 'href="tema.css"' in land
    assert 'href="../../static/css/base.css"' in card and 'href="../tema.css"' in card
    assert 'content="https://davy.netlify.app/completo/img/capa-8.webp"' in land
    assert 'src="img/completo/capa-8.webp"' in _html(d / "index.html")


def test_og_cliente(raiz, tmp_path, monkeypatch):
    monkeypatch.setattr(build, "RAIZ", raiz)
    d = tmp_path / "dist"
    assert build.main(["--site", "completo", "--saida", str(d)]) == 0
    assert 'content="https://davy.netlify.app/img/capa-8.webp"' in _html(d / "index.html")


def test_recusa_saida_perigosa(raiz, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(build, "RAIZ", raiz)
    nao_gerado = tmp_path / "outro"
    nao_gerado.mkdir()
    (nao_gerado / "x.txt").write_text("meu")
    for s in (raiz, raiz.parent, raiz / "sites", nao_gerado):
        assert build.main(["--saida", str(s)]) == 1
        assert "recusado" in capsys.readouterr().err
    assert (raiz / "sites" / "completo" / "site.toml").is_file() and (nao_gerado / "x.txt").is_file()


def test_dados_invalidos_preservam_dist(raiz, tmp_path, monkeypatch, editar):
    monkeypatch.setattr(build, "RAIZ", raiz)
    d = tmp_path / "dist"
    assert build.main(["--saida", str(d)]) == 0
    editar("preco = 5", 'preco = "cinco"')
    assert build.main(["--saida", str(d)]) == 1
    assert (d / "index.html").is_file()
