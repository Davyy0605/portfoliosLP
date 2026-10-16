"""Baixa as fotos listadas em [[fotos]] do site.toml para <pasta>/imagens/."""
import sys
import tomllib
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

UA = "Mozilla/5.0 (compatible; cardapios-baixar-fotos/1.0)"


def url_final(url: str) -> str:
    p = urlparse(url)
    host = p.hostname or ""
    if (host == "unsplash.com" or host.endswith(".unsplash.com")) and not p.query:
        return url + "?w=2000&q=85&fm=jpg"
    return url


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("uso: python ferramentas/baixar_fotos.py <pasta do site>")
        return 2
    pasta = Path(argv[0])
    try:
        with open(pasta / "site.toml", "rb") as f:
            fotos = tomllib.load(f).get("fotos", [])
    except (OSError, tomllib.TOMLDecodeError) as e:
        print(f"erro: não foi possível ler {pasta / 'site.toml'}: {e}")
        return 1
    (pasta / "imagens").mkdir(exist_ok=True)
    falhas = 0
    for i, foto in enumerate(fotos):
        arquivo, url = foto.get("arquivo"), foto.get("url")
        if not arquivo or not url:
            falhas += 1
            print(f"site.toml: fotos[{i}]: entrada sem arquivo/url")
            continue
        destino = pasta / "imagens" / arquivo
        if destino.exists():
            print(f"já existe: {arquivo}")
            continue
        tmp = destino.with_name(destino.name + ".part")
        try:
            req = urllib.request.Request(url_final(url), headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                tipo = r.headers.get("Content-Type", "")
                if not tipo.startswith("image/"):
                    raise ValueError(f"resposta não é imagem (Content-Type: {tipo or 'ausente'})")
                tmp.write_bytes(r.read())
            tmp.replace(destino)
            print(f"baixada: {arquivo}")
        except Exception as e:  # rede, HTTP, URL inválida
            tmp.unlink(missing_ok=True)
            falhas += 1
            print(f"erro ao baixar {arquivo} ({url}): {e}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
