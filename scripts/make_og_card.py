"""Render static/og-card.png (1200x630) with the vendored brand fonts. Local tool, run once;
the PNG is committed. Needs Pillow + fontTools (woff2 -> ttf in memory). Carries the
synthetic-data label the fleet OG rollout requires (fleet-ops OG-ROLLOUT-2026-09-04).
"""

import io
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "static" / "lailara" / "fonts"


def font(name, size):
    f = TTFont(FONTS / name)
    f.flavor = None
    buf = io.BytesIO()
    f.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + [cur]


def main():
    W, H, PAD = 1200, 630, 72
    img = Image.new("RGB", (W, H), "#f5f3ee")
    d = ImageDraw.Draw(img)
    eyebrow = font("source-sans-3-latin-600.woff2", 24)
    head = font("playfair-display-latin-700.woff2", 76)
    sub = font("source-sans-3-latin.woff2", 32)
    foot = font("source-sans-3-latin-600.woff2", 22)

    d.text((PAD, PAD), "LAILARA LLC", font=eyebrow, fill="#cc100a")
    d.line([(PAD, PAD + 40), (W - PAD, PAD + 40)], fill="#cc100a", width=1)
    d.text((PAD, PAD + 78), "Campaign Math", font=head, fill="#0d0d0d")
    y = PAD + 190
    for line in wrap(d, "Four transparent attribution rules and a tracking-hygiene audit. Which campaigns "
                        "worked, and can the data even answer that?", sub, W - 2 * PAD):
        d.text((PAD, y), line, font=sub, fill="#333333")
        y += 44
    d.line([(PAD, H - PAD - 34), (W - PAD, H - PAD - 34)], fill="#d9d9d9", width=1)
    d.text((PAD, H - PAD - 20), "campaignmath.lailarallc.com", font=foot, fill="#595959")
    label = "WORKED EXAMPLE · SYNTHETIC DATA"
    d.text((W - PAD - d.textlength(label, font=foot), H - PAD - 20), label, font=foot, fill="#595959")
    out = ROOT / "static" / "og-card.png"
    img.save(out, optimize=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
