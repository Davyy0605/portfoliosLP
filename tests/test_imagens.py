import os
import sys
from pathlib import Path

from PIL import Image

from gerador.imagens import otimizar_imagens

sys.path.insert(0, str(Path(__file__).parent.parent / "ferramentas"))
from baixar_fotos import url_final  # noqa: E402


def _img(p, tam, modo="RGB"):
    Image.new(modo, tam, "red").save(p)


def test_duas_variantes(tmp_path):
    o, d = tmp_path / "o", tmp_path / "img"
    o.mkdir()
    _img(o / "capa.jpg", (3000, 2000))
    r = otimizar_imagens(o, d)
    assert (d / "capa-800.webp").exists() and (d / "capa-1600.webp").exists()
    assert r["capa.jpg"] == {
        "src": "img/capa-1600.webp",
        "srcset": "img/capa-800.webp 800w, img/capa-1600.webp 1600w",
        "largura": 1600,
        "altura": 1067,
    }


def test_nao_amplia(tmp_path):
    o, d = tmp_path / "o", tmp_path / "img"
    o.mkdir()
    _img(o / "p.jpg", (600, 400))
    r = otimizar_imagens(o, d)["p.jpg"]
    assert sorted(x.name for x in d.iterdir()) == ["p-600.webp"]
    assert r["largura"] == 600 and r["altura"] == 400
    assert r["srcset"] == "img/p-600.webp 600w"


def test_png_transparente(tmp_path):
    o, d = tmp_path / "o", tmp_path / "img"
    o.mkdir()
    _img(o / "t.png", (100, 100), "RGBA")
    assert "t.png" in otimizar_imagens(o, d)


def test_nao_regera(tmp_path):
    o, d = tmp_path / "o", tmp_path / "img"
    o.mkdir()
    _img(o / "c.jpg", (900, 600))
    otimizar_imagens(o, d)
    arq = d / "c-800.webp"
    os.utime(arq, (1, 1))
    os.utime(o / "c.jpg", (0, 0))  # origem mais antiga que o webp
    otimizar_imagens(o, d)
    assert arq.stat().st_mtime == 1


def test_url_unsplash_ganha_query():
    u = "https://images.unsplash.com/photo-1"
    assert url_final(u) == u + "?w=1600&q=85&fm=jpg"
    com = u + "?w=500"
    assert url_final(com) == com
    assert url_final("https://pexels.com/x.jpg") == "https://pexels.com/x.jpg?auto=compress&w=1600"


def test_host_unsplash_exato():
    assert url_final("https://notunsplash.com/a").endswith("/a")
    assert "w=1600" in url_final("https://unsplash.com/a")


class _Resp:
    def __init__(self, tipo, corpo=b"x"):
        self.headers = {"Content-Type": tipo}
        self._c = corpo

    def read(self, n=-1):
        return self._c if n < 0 else self._c[:n]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def _site(tmp_path, fotos_toml):
    (tmp_path / "site.toml").write_text(fotos_toml, encoding="utf-8")
    return tmp_path


def test_baixar_entrada_incompleta(tmp_path, capsys):
    import baixar_fotos
    pasta = _site(tmp_path, '[[fotos]]\nurl = "https://x/a.jpg"\n')
    assert baixar_fotos.main([str(pasta)]) == 1
    assert "fotos[0]: entrada sem arquivo/url" in capsys.readouterr().out


def test_baixar_rejeita_nao_imagem(tmp_path, monkeypatch):
    import baixar_fotos
    pasta = _site(tmp_path, '[[fotos]]\narquivo = "a.jpg"\nurl = "https://x/a"\n')
    monkeypatch.setattr(baixar_fotos.urllib.request, "urlopen", lambda *a, **k: _Resp("text/html"))
    assert baixar_fotos.main([str(pasta)]) == 1
    assert list((pasta / "imagens").iterdir()) == []


def test_baixar_ok(tmp_path, monkeypatch):
    import baixar_fotos
    pasta = _site(tmp_path, '[[fotos]]\narquivo = "a.jpg"\nurl = "https://x/a"\n')
    monkeypatch.setattr(baixar_fotos.urllib.request, "urlopen", lambda *a, **k: _Resp("image/jpeg", b"img"))
    assert baixar_fotos.main([str(pasta)]) == 0
    assert (pasta / "imagens" / "a.jpg").read_bytes() == b"img"


def test_baixar_rejeita_arquivo_com_caminho(tmp_path, monkeypatch):
    import baixar_fotos
    monkeypatch.setattr(baixar_fotos.urllib.request, "urlopen", lambda *a, **k: _Resp("image/jpeg", b"img"))
    for nome in ("../x.jpg", "a/b.jpg", "a" + chr(92) + "b.jpg", ".."):
        pasta = _site(tmp_path, f"[[fotos]]\narquivo = '{nome}'\nurl = 'https://x/a'\n")
        assert baixar_fotos.main([str(pasta)]) == 1
    assert not (tmp_path / "x.jpg").exists() and list((tmp_path / "imagens").iterdir()) == []


def test_baixar_limita_tamanho(tmp_path, monkeypatch):
    import baixar_fotos
    pasta = _site(tmp_path, '[[fotos]]\narquivo = "a.jpg"\nurl = "https://x/a"\n')
    monkeypatch.setattr(baixar_fotos, "LIMITE", 10)
    monkeypatch.setattr(baixar_fotos.urllib.request, "urlopen", lambda *a, **k: _Resp("image/jpeg", b"x" * 11))
    assert baixar_fotos.main([str(pasta)]) == 1
    assert list((pasta / "imagens").iterdir()) == []


def test_cache_nao_reconverte_e_copia(tmp_path, monkeypatch):
    o, c = tmp_path / "o", tmp_path / "cache"
    o.mkdir()
    _img(o / "c.jpg", (900, 600))
    r1 = otimizar_imagens(o, tmp_path / "d1" / "img", cache=c)
    chamadas = []
    orig = Image.Image.save
    monkeypatch.setattr(Image.Image, "save", lambda self, *a, **k: (chamadas.append(1), orig(self, *a, **k))[1])
    r2 = otimizar_imagens(o, tmp_path / "d2" / "img", cache=c)
    assert chamadas == [] and r1 == r2
    assert (tmp_path / "d2" / "img" / "c-800.webp").is_file() and (tmp_path / "d2" / "img" / "c-900.webp").is_file()


def test_arquivos_restringe(tmp_path):
    o, d = tmp_path / "o", tmp_path / "img"
    o.mkdir()
    _img(o / "a.jpg", (100, 100))
    _img(o / "b.jpg", (100, 100))
    r = otimizar_imagens(o, d, arquivos=["a.jpg"])
    assert list(r) == ["a.jpg"] and [x.name for x in d.iterdir()] == ["a-100.webp"]


def test_exif_rotaciona_dimensoes_frio_e_quente(tmp_path):
    o, c = tmp_path / "o", tmp_path / "cache"
    o.mkdir()
    im = Image.new("RGB", (900, 600), "red")
    ex = Image.Exif()
    ex[0x0112] = 6
    im.save(o / "r.jpg", exif=ex)
    for d in ("d1", "d2"):  # frio, depois cache hit
        r = otimizar_imagens(o, tmp_path / d / "img", cache=c)["r.jpg"]
        assert (r["largura"], r["altura"]) == (600, 900)
    with Image.open(c / "r-600.webp") as w:
        assert w.size == (600, 900)
