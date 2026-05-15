"""Generate HA-brands assets from the official Vacmaster logo PNG.

Input:  .brand-source.png (gitignored)
Output: brand_assets/{icon,icon@2x,logo,logo@2x,dark_logo,dark_logo@2x}.png

Strategy:
- The source is the combined "blue swirl + black Vacmaster wordmark" logo.
- Icon  = bounding box of the blue pixels only (just the swirl), padded
          square, scaled to 256/512.
- Logo  = bounding box of all opaque pixels (swirl + wordmark), scaled
          to a height of 256/512 (shortest side within the HA spec).
- Dark  = wordmark recoloured to white, swirl untouched (blue reads
          fine on both light and dark backgrounds, so we skip dark_icon
          and let HA's auto-fallback to icon.png cover that case).
"""

from pathlib import Path

import numpy as np
from PIL import Image


SOURCE = Path(".brand-source.png")
OUT = Path("brand_assets")
OUT.mkdir(exist_ok=True)


def is_blue(rgb: np.ndarray) -> np.ndarray:
    """Mask of pixels where blue clearly dominates (i.e. the swirl)."""
    return (
        (rgb[..., 2] > 100)
        & (rgb[..., 2] > rgb[..., 0] * 1.4)
        & (rgb[..., 2] > rgb[..., 1] * 1.4)
    )


def crop_bbox(img: Image.Image, mask: np.ndarray) -> Image.Image:
    """Crop the image to the bounding box of the True pixels in ``mask``."""
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return img
    return img.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def square_pad(img: Image.Image) -> Image.Image:
    """Pad an image with transparent pixels until it is square."""
    w, h = img.size
    side = max(w, h)
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.paste(img, ((side - w) // 2, (side - h) // 2))
    return out


def to_dark(img: Image.Image) -> Image.Image:
    """Return a copy where the non-blue ink is recoloured to white."""
    arr = np.array(img).copy()
    rgb = arr[..., :3]
    alpha = arr[..., 3]
    not_blue = ~is_blue(rgb)
    ink = not_blue & (alpha > 0)
    arr[ink, 0] = 255
    arr[ink, 1] = 255
    arr[ink, 2] = 255
    return Image.fromarray(arr)


def save(img: Image.Image, name: str) -> None:
    """Save PNG with interlace + lossless compression as the HA spec asks."""
    img.save(OUT / name, optimize=True, interlace=True)
    print(f"  {name}: {img.size}, {(OUT / name).stat().st_size} bytes")


def _strip_white_background(img: Image.Image) -> Image.Image:
    """Make near-white pixels transparent.

    The Vacmaster brand assets we ship from seeklogo are mode-P PNGs with a
    solid white background rather than transparency, which would make the
    bounding-box crops degenerate to the full canvas.
    """
    arr = np.array(img).copy()
    rgb = arr[..., :3]
    near_white = (
        (rgb[..., 0] > 240) & (rgb[..., 1] > 240) & (rgb[..., 2] > 240)
    )
    arr[near_white, 3] = 0
    return Image.fromarray(arr)


def main() -> None:
    """Generate the six brand assets."""
    src = _strip_white_background(Image.open(SOURCE).convert("RGBA"))
    arr = np.array(src)
    rgb = arr[..., :3]
    alpha = arr[..., 3]

    # ICON = blue swirl only.
    icon_src = crop_bbox(src, is_blue(rgb) & (alpha > 10))
    icon_sq = square_pad(icon_src)
    save(icon_sq.resize((256, 256), Image.LANCZOS), "icon.png")
    save(icon_sq.resize((512, 512), Image.LANCZOS), "icon@2x.png")

    # LOGO (light) = swirl + black wordmark, scaled to height 256 / 512.
    logo_src = crop_bbox(src, alpha > 10)
    lw, lh = logo_src.size
    logo_256 = logo_src.resize((lw * 256 // lh, 256), Image.LANCZOS)
    logo_512 = logo_src.resize((lw * 512 // lh, 512), Image.LANCZOS)
    save(logo_256, "logo.png")
    save(logo_512, "logo@2x.png")

    # LOGO (dark) = swirl + WHITE wordmark.
    save(to_dark(logo_256), "dark_logo.png")
    save(to_dark(logo_512), "dark_logo@2x.png")


if __name__ == "__main__":
    main()
