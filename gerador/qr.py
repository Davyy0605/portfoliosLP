"""QR code em SVG inline."""
import re

import segno


def qr_svg(url: str) -> str:
    svg = segno.make(url, error="m").svg_inline(scale=4, border=2, dark="#1a1a1a", omitsize=True)
    lado = int(re.search(r'viewBox="0 0 (\d+) ', svg).group(1)) // 4  # módulos (com borda); o viewBox vem multiplicado por scale=4
    # crispEdges evita bordas borradas; --m deixa o CSS dimensionar em múltiplos inteiros de pixel por módulo
    return svg.replace('class="segno"', f'class="segno" shape-rendering="crispEdges" style="--m:{lado}"', 1)
