import shutil
from pathlib import Path

import pytest
from PIL import Image

FIXTURE = Path(__file__).parent / "fixtures" / "completo"


@pytest.fixture
def temas_dir(tmp_path):
    (tmp_path / "temas" / "teste").mkdir(parents=True)
    return tmp_path / "temas"


@pytest.fixture
def site_dir(tmp_path):
    """Cópia da fixture com imagens JPG pequenas geradas na hora."""
    pasta = tmp_path / "sites" / "completo"
    pasta.mkdir(parents=True)
    shutil.copy(FIXTURE / "site.toml", pasta / "site.toml")
    (pasta / "imagens").mkdir()
    for nome in ("capa.jpg", "a.jpg"):
        Image.new("RGB", (8, 8), "red").save(pasta / "imagens" / nome)
    return pasta


@pytest.fixture
def editar(site_dir):
    """editar(antigo, novo): troca texto no site.toml da cópia."""
    def _editar(antigo, novo):
        arq = site_dir / "site.toml"
        txt = arq.read_text(encoding="utf-8")
        assert antigo in txt
        arq.write_text(txt.replace(antigo, novo, 1), encoding="utf-8")
    return _editar


@pytest.fixture
def raiz(site_dir):
    """Raiz de projeto temporária: temas/, static/, config.toml reais + sites/completo."""
    base = site_dir.parent.parent
    real = Path(__file__).parent.parent
    shutil.copytree(real / "temas", base / "temas", dirs_exist_ok=True)
    shutil.copytree(real / "static", base / "static")
    shutil.copy(real / "config.toml", base / "config.toml")
    return base
