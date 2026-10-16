"""Otimização de imagens: WebP em várias larguras + srcset."""
import shutil
from collections.abc import Iterable
from pathlib import Path

from PIL import Image, ImageOps

EXTENSOES = {".jpg", ".jpeg", ".png", ".webp"}


def otimizar_imagens(origem: Path, destino: Path, larguras: tuple[int, ...] = (800, 1600),
                     arquivos: Iterable[str] | None = None, cache: Path | None = None) -> dict[str, dict]:
    """Gera WebP em `cache` (se dado; senão direto em `destino`) e copia para `destino`.

    `arquivos` restringe a otimização a esses nomes (padrão: a pasta inteira).
    """
    origem, destino = Path(origem), Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    gerar_em = Path(cache) if cache else destino
    gerar_em.mkdir(parents=True, exist_ok=True)
    nomes = None if arquivos is None else set(arquivos)
    saida = {}
    for arq in sorted(origem.iterdir()):
        if arq.suffix.lower() not in EXTENSOES or (nomes is not None and arq.name not in nomes):
            continue
        with Image.open(arq) as im:
            w0, h0 = im.size  # sem decodificar; só troca se a orientação EXIF girar 90 graus
            if im.getexif().get(0x0112) in (5, 6, 7, 8):
                w0, h0 = h0, w0
            transposta = None
            ws = sorted({min(w, w0) for w in larguras})
            for w in ws:
                alvo = gerar_em / f"{arq.stem}-{w}.webp"
                if not (alvo.exists() and alvo.stat().st_mtime >= arq.stat().st_mtime):
                    if transposta is None:
                        transposta = ImageOps.exif_transpose(im)
                    v = transposta.convert("RGBA" if im.mode in ("RGBA", "LA", "P") else "RGB")
                    v = v.resize((w, round(h0 * w / w0)), Image.LANCZOS)
                    v.save(alvo, "WEBP", quality=78)
                if gerar_em != destino:
                    shutil.copyfile(alvo, destino / alvo.name)
        pasta = destino.name
        saida[arq.name] = {
            "src": f"{pasta}/{arq.stem}-{ws[-1]}.webp",
            "srcset": ", ".join(f"{pasta}/{arq.stem}-{w}.webp {w}w" for w in ws),
            "largura": ws[-1],
            "altura": round(h0 * ws[-1] / w0),
        }
    return saida
