"""Baixa as fotos listadas em [[fotos]] do site.toml para <pasta>/imagens/."""
import sys
import tomllib
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

LIMITE = 25 * 1024 * 1024
UA = "Mozilla/5.0 (compatible; cardapios-baixar-fotos/1.0)"


def url_final(url: str) -> str:
    p = urlparse(url)
    host = p.hostname or ""
    if p.query:
        return url
    if host == "unsplash.com" or host.endswith(".unsplash.com"):
        return url + "?w=1600&q=85&fm=jpg"
    if host == "pexels.com" or host.endswith(".pexels.com"):
        return url + "?auto=compress&w=1600"
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
        if arquivo in (".", "..") or Path(arquivo).name != arquivo or "\\" in arquivo:
            falhas += 1
            print(f"site.toml: fotos[{i}]: arquivo {arquivo!r} não pode conter caminho")
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
                corpo = r.read(LIMITE + 1)
                if len(corpo) > LIMITE:
                    raise ValueError(f"download maior que {LIMITE // 1024 // 1024} MB")
                tmp.write_bytes(corpo)
            tmp.replace(destino)
            print(f"baixada: {arquivo}")
        except Exception as e:  # rede, HTTP, URL inválida
            tmp.unlink(missing_ok=True)
            falhas += 1
            print(f"erro ao baixar {arquivo} ({url}): {e}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
