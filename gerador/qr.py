"""QR code em SVG inline."""
import segno


def qr_svg(url: str) -> str:
    return segno.make(url, error="m").svg_inline(scale=4, border=2, dark="#1a1a1a", omitsize=True)
