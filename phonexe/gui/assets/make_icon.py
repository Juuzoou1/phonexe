"""
Generate the phonexe application icon (offline, no bundled art needed).

Draws the brand mark — a neon cyan phone outline with a scan line on a dark
rounded-square, matching the design system (level0 background #050B12, accent
#4FE3E0) — and writes both a multi-resolution Windows ``appicon.ico`` and a
``appicon.png`` next to this file.

Run:  python -m phonexe.gui.assets.make_icon
The result is committed so the packaged EXE / installer / GUI window all share
one identity without re-rendering at build time.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

_BG0 = (5, 11, 18, 255)        # level0
_BG1 = (13, 23, 36, 255)       # level2 (inner panel)
_BORDER = (20, 48, 74, 255)    # border #14304A
_ACCENT = (79, 227, 224, 255)  # accent #4FE3E0
_ACCENT_SOFT = (79, 227, 224, 90)


def _rounded(draw: ImageDraw.ImageDraw, box, radius, **kw):
    draw.rounded_rectangle(box, radius=radius, **kw)


def render(size: int = 512) -> Image.Image:
    """Render the icon at *size* px (designed at 512, scales cleanly down)."""
    s = size
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Rounded-square badge: dark base with a 1px-ish cyan border.
    pad = int(s * 0.06)
    _rounded(d, (pad, pad, s - pad, s - pad), radius=int(s * 0.22),
             fill=_BG0)
    _rounded(d, (pad, pad, s - pad, s - pad), radius=int(s * 0.22),
             outline=_BORDER, width=max(2, s // 110))

    # Phone body, centered, portrait.
    pw, ph = int(s * 0.34), int(s * 0.56)
    px0 = (s - pw) // 2
    py0 = (s - ph) // 2
    phone_box = (px0, py0, px0 + pw, py0 + ph)
    radius = int(pw * 0.26)

    # Glow pass: draw the outline thick on a separate layer and blur it.
    glow = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    _rounded(gd, phone_box, radius=radius, outline=_ACCENT,
             width=max(4, s // 40))
    glow = glow.filter(ImageFilter.GaussianBlur(s // 45))
    img.alpha_composite(glow)

    # Inner screen fill, then crisp neon outline.
    _rounded(d, phone_box, radius=radius, fill=_BG1)
    _rounded(d, phone_box, radius=radius, outline=_ACCENT,
             width=max(2, s // 90))

    # Notch.
    nw = int(pw * 0.42)
    nx0 = (s - nw) // 2
    ny0 = py0 + int(ph * 0.045)
    _rounded(d, (nx0, ny0, nx0 + nw, ny0 + int(s * 0.022)),
             radius=int(s * 0.012), fill=_ACCENT)

    # Scan line sweeping across the screen (the forensic "scanning" motif).
    ly = py0 + int(ph * 0.52)
    inset = int(pw * 0.14)
    d.line((px0 + inset, ly, px0 + pw - inset, ly), fill=_ACCENT,
           width=max(3, s // 70))
    # soft halo above/below the scan line
    halo = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    hd.line((px0 + inset, ly, px0 + pw - inset, ly), fill=_ACCENT_SOFT,
            width=max(8, s // 26))
    halo = halo.filter(ImageFilter.GaussianBlur(s // 60))
    img.alpha_composite(halo)

    # Home indicator.
    hw = int(pw * 0.30)
    hx0 = (s - hw) // 2
    hy0 = py0 + ph - int(s * 0.05)
    _rounded(d, (hx0, hy0, hx0 + hw, hy0 + int(s * 0.012)),
             radius=int(s * 0.006), fill=_ACCENT_SOFT)
    return img


def build(dest: Path | None = None) -> Path:
    here = dest or Path(__file__).resolve().parent
    here.mkdir(parents=True, exist_ok=True)
    master = render(512)
    png_path = here / "appicon.png"
    ico_path = here / "appicon.ico"
    master.save(png_path)
    # Windows .ico with the standard resolution set.
    master.save(
        ico_path,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
               (128, 128), (256, 256)],
    )
    return ico_path


if __name__ == "__main__":  # pragma: no cover
    out = build()
    print("Wrote", out, "and", out.with_suffix(".png"))
