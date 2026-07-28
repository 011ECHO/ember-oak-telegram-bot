"""Product-card image generation (used by the dev tool and at runtime).

Draws one clean placeholder card per product (wordmark, emoji in a disc, name,
price badge). Called when a product is created or its name/price/emoji change so
the card always matches the current data. Requires Pillow.

Cross-platform note: uses Windows system fonts when present and falls back to a
default font otherwise, so a missing emoji font degrades gracefully instead of
crashing.
"""

import os

from PIL import Image, ImageDraw, ImageFont

W, H = 1000, 750
CREAM = (251, 246, 239)

_FONTS = "C:/Windows/Fonts"
_FONT_NAME = f"{_FONTS}/seguisb.ttf"
_FONT_BOLD = f"{_FONTS}/segoeuib.ttf"
_FONT_EMOJI = f"{_FONTS}/seguiemj.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _gradient(top, bottom) -> Image.Image:
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        row = _mix(top, bottom, y / (H - 1))
        for x in range(W):
            px[x, y] = row
    return img


def _center(draw, text, font, y, fill, **kw):
    box = draw.textbbox((0, 0), text, font=font, **kw)
    draw.text(((W - (box[2] - box[0])) / 2 - box[0], y), text, font=font, fill=fill, **kw)


def generate_card(product_id: str, name: str, price: float, emoji: str,
                  accent: str, out_dir: str) -> str:
    """Render a product card to ``<out_dir>/<product_id>.png`` and return the path."""
    accent_rgb = _hex(accent)
    img = _gradient(CREAM, accent_rgb)
    draw = ImageDraw.Draw(img)

    _center(draw, "E M B E R   &   O A K", _font(_FONT_NAME, 34), 54, (110, 90, 74))

    # Emoji in a soft white disc (embedded colour when the emoji font is present).
    cx, cy, r = W // 2, 315, 175
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255))
    emoji_font = _font(_FONT_EMOJI, 200)
    try:
        box = draw.textbbox((0, 0), emoji, font=emoji_font, embedded_color=True)
        draw.text((cx - (box[2] - box[0]) / 2 - box[0], cy - (box[3] - box[1]) / 2 - box[1]),
                  emoji, font=emoji_font, embedded_color=True)
    except Exception:
        pass  # emoji font unavailable — leave the disc plain

    _center(draw, name, _font(_FONT_BOLD, 76), 545, (46, 42, 38))

    # Price badge.
    price_text = f"€{price:.2f}"
    pf = _font(_FONT_BOLD, 46)
    pb = draw.textbbox((0, 0), price_text, font=pf)
    pw, ph = pb[2] - pb[0], pb[3] - pb[1]
    bw, bh = pw + 80, ph + 44
    bx, by = (W - bw) / 2, 650
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=bh / 2, fill=(255, 255, 255))
    draw.text((bx + (bw - pw) / 2 - pb[0], by + (bh - ph) / 2 - pb[1]),
              price_text, font=pf, fill=accent_rgb)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{product_id}.png")
    img.save(path, "PNG")
    return path
