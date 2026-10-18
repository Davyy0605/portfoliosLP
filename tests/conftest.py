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
    """Raiz de projeto temporária: temas/, static/ reais + config.toml próprio + sites/completo."""
    base = site_dir.parent.parent
    real = Path(__file__).parent.parent
    shutil.copytree(real / "temas", base / "temas", dirs_exist_ok=True)
    shutil.copytree(real / "static", base / "static")
    # Config provisória própria: testes não devem depender do número/URL reais do dono.
    (base / "config.toml").write_text(
        'url_base = "https://davy.netlify.app/"\n'
        'whatsapp = "5500000000000"\n'
        '\n'
        '[marca]\n'
        'nome = "Davy"\n'
        'cor = "#7C3AED"\n',
        encoding="utf-8",
    )
    return base


FIXTURE_BELEZA = Path(__file__).parent / "fixtures" / "beleza"


@pytest.fixture
def site_beleza(tmp_path):
    """Cópia da fixture de beleza em sites/studio-teste/, com imagens geradas."""
    pasta = tmp_path / "sites" / "studio-teste"
    pasta.mkdir(parents=True)
    shutil.copy(FIXTURE_BELEZA / "site.toml", pasta / "site.toml")
    (pasta / "imagens").mkdir()
    for nome in ("capa.jpg", "a.jpg"):
        Image.new("RGB", (8, 8), "red").save(pasta / "imagens" / nome)
    return pasta
