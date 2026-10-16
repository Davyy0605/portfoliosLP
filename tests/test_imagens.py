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
    assert url_final(u) == u + "?w=2000&q=85&fm=jpg"
    com = u + "?w=500"
    assert url_final(com) == com
    assert url_final("https://pexels.com/x.jpg") == "https://pexels.com/x.jpg"
