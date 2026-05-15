"""Generate HA-brands assets for vacmaster_cardio54 — original design.

To stay clear of any Vacmaster-trademark concerns, this script does NOT
reproduce the official swirl logotype. Instead the icon is a fresh,
geometrically constructed RF-broadcast mark — concentric rings around a
central dot, evoking the radio-frequency transmission the integration
actually does. The wordmark is plain text "Vacmaster" rendered in a
freely licensed sans-serif (DejaVu Sans Bold) so we never reproduce
Vacmaster's custom typeface either.

Result: a brand mark that's recognisably about the integration purpose
(RF control of a Vacmaster Cardio54 fan), but visually + typographically
distinct from Vacmaster's own brand identity.

Output: brand_assets/{icon,icon@2x,logo,logo@2x,
                    dark_logo,dark_logo@2x}.png

dark_icon is intentionally not produced — the blue ring mark reads on
both light and dark backgrounds, so HA-Brands' "fall back to the
non-prefixed asset" rule covers dark themes for free.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LOGO_TEXT = "Vacmaster"

# Vacmaster-like blue, but standard CSS "denim" rather than their pantone.
COLOR_BLUE = (0, 115, 188, 255)

OUT = Path("brand_assets")
OUT.mkdir(exist_ok=True)


def _render_icon(work_px: int = 2048) -> Image.Image:
    """Render the RF-broadcast mark at ``work_px``×``work_px``.

    Geometry: three concentric rings + a central dot. The rings sit at
    radii 22 %, 32 % and 42 % of the canvas, each drawn with a constant
    8 % stroke. The central dot is 5 %. All proportions chosen so the
    full mark reads at 32 px without losing detail.
    """
    img = Image.new("RGBA", (work_px, work_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx = cy = work_px // 2
    stroke = max(1, int(work_px * 0.06))

    for r_ratio in (0.22, 0.32, 0.42):
        r = work_px * r_ratio
        draw.ellipse(
            (cx - r, cy - r, cx + r, cy + r), outline=COLOR_BLUE, width=stroke
        )

    r_dot = work_px * 0.06
    draw.ellipse(
        (cx - r_dot, cy - r_dot, cx + r_dot, cy + r_dot), fill=COLOR_BLUE
    )

    return img.crop(img.getbbox())


def _square_pad(img: Image.Image) -> Image.Image:
    """Pad ``img`` with transparent pixels until it is square."""
    w, h = img.size
    side = max(w, h)
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return out


def _render_text(text: str, color: tuple[int, int, int, int]) -> Image.Image:
    """Render ``text`` very large, then crop to the ink bbox."""
    work_px = 2400
    font = ImageFont.truetype(FONT_PATH, work_px)
    sandbox = Image.new("RGBA", (work_px * 6, work_px * 2), (0, 0, 0, 0))
    ImageDraw.Draw(sandbox).text(
        (work_px, work_px // 2), text, font=font, fill=color
    )
    return sandbox.crop(sandbox.getbbox())


def _composite(left: Image.Image, right: Image.Image) -> Image.Image:
    """Stack two PIL images side by side, vertically centred, with a gap."""
    gap = left.width // 5
    width = left.width + gap + right.width
    height = max(left.height, right.height)
    out = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    out.paste(left, (0, (height - left.height) // 2), left)
    out.paste(right, (left.width + gap, (height - right.height) // 2), right)
    return out


def _save(img: Image.Image, name: str) -> None:
    """Save PNG, optimised, log dimensions + final size."""
    img.save(OUT / name, optimize=True)
    print(f"  {name:25s}  {img.size}  {(OUT / name).stat().st_size:>7} bytes")


def main() -> None:
    """Generate the six brand assets."""
    # === ICON: concentric ring mark, isolated + square-padded ===
    icon_hi = _square_pad(_render_icon())
    _save(icon_hi.resize((256, 256), Image.LANCZOS), "icon.png")
    _save(icon_hi.resize((512, 512), Image.LANCZOS), "icon@2x.png")

    # === LOGO: icon + ``Vacmaster`` wordmark in DejaVu Sans Bold ===
    for target_height, suffix in ((256, ""), (512, "@2x")):
        # Icon at the same height as the wordmark.
        iw, ih = icon_hi.size
        icon_h = icon_hi.resize(
            (iw * target_height // ih, target_height), Image.LANCZOS
        )
        # Wordmark a touch smaller so its cap-height matches the icon's
        # visual bounding circle (the icon has a thin pixel margin).
        text_h = int(target_height * 0.78)
        for color, prefix in (((0, 0, 0, 255), ""), ((255, 255, 255, 255), "dark_")):
            wm_hi = _render_text(LOGO_TEXT, color)
            ww, wh = wm_hi.size
            wm = wm_hi.resize((ww * text_h // wh, text_h), Image.LANCZOS)
            _save(_composite(icon_h, wm), f"{prefix}logo{suffix}.png")


if __name__ == "__main__":
    main()
