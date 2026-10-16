"""Baixa as fotos listadas em [[fotos]] do site.toml para <pasta>/imagens/."""
import sys
import tomllib
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

UA = "Mozilla/5.0 (compatible; cardapios-baixar-fotos/1.0)"


def url_final(url: str) -> str:
    p = urlparse(url)
    if p.hostname and p.hostname.endswith("unsplash.com") and not p.query:
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
    for foto in fotos:
        destino = pasta / "imagens" / foto["arquivo"]
        if destino.exists():
            print(f"já existe: {foto['arquivo']}")
            continue
        try:
            req = urllib.request.Request(url_final(foto["url"]), headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                destino.write_bytes(r.read())
            print(f"baixada: {foto['arquivo']}")
        except Exception as e:  # rede, HTTP, URL inválida
            falhas += 1
            print(f"erro ao baixar {foto['arquivo']} ({foto['url']}): {e}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
