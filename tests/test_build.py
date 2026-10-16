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
