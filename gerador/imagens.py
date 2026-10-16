"""Otimização de imagens: WebP em várias larguras + srcset."""
from pathlib import Path

from PIL import Image, ImageOps

EXTENSOES = {".jpg", ".jpeg", ".png", ".webp"}


def otimizar_imagens(origem: Path, destino: Path, larguras: tuple[int, ...] = (800, 1600)) -> dict[str, dict]:
    origem, destino = Path(origem), Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    saida = {}
    for arq in sorted(origem.iterdir()):
        if arq.suffix.lower() not in EXTENSOES:
            continue
        with Image.open(arq) as im:
            im = ImageOps.exif_transpose(im)
            w0, h0 = im.size
            ws = sorted({min(w, w0) for w in larguras})
            for w in ws:
                alvo = destino / f"{arq.stem}-{w}.webp"
                if alvo.exists() and alvo.stat().st_mtime >= arq.stat().st_mtime:
                    continue
                v = im.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
                v = v.resize((w, round(h0 * w / w0)), Image.LANCZOS)
                v.save(alvo, "WEBP", quality=78)
        pasta = destino.name
        saida[arq.name] = {
            "src": f"{pasta}/{arq.stem}-{ws[-1]}.webp",
            "srcset": ", ".join(f"{pasta}/{arq.stem}-{w}.webp {w}w" for w in ws),
            "largura": ws[-1],
            "altura": round(h0 * ws[-1] / w0),
        }
    return saida
