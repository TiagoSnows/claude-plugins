"""Cut a Flow icon sheet (flat blue or green background, R x C grid) into square RGBA icons.

    python cut_icons.py <sheet> <out_dir> --grid 2x3 --names a b c d e f [--key auto|blue|green]
                        [--bleed 0] [--size 256] [--fill 0.85]

Each cell keeps its main blob and every detached part inside the cell (sparkles, sound waves); pieces touching the
cell border that are not the main blob are dropped, since that is how a neighbour's overflow looks. Image models
do not respect grid lines: a hat brim or a puff of steam often crosses into the next cell and comes out cut
straight. --bleed N widens every cell by N px on each side before picking the main blob, which recovers those
parts (try 40-80 on a 1024 px sheet when a cut edge looks straight). A name "-" skips that cell.
The icon is centred on a transparent square, the object filling --fill of the side.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))  # sibling import that also works with python -I
from chroma import key_out, resize_rgba


def main_blob(cell: np.ndarray) -> np.ndarray:
    """Keep the largest blob and the detached parts that float inside the cell; zero the alpha of other blobs that
    touch the cell border (a neighbour's overflow). Blobs are slightly grown so their soft edges stay."""
    out = cell.copy()
    solid = out[..., 3] > 128
    labels, n = ndimage.label(ndimage.binary_dilation(solid, iterations=6))
    if n > 1:
        sizes = ndimage.sum(solid, labels, range(1, n + 1))
        main_label = int(np.argmax(sizes)) + 1
        band = np.zeros_like(solid)
        band[:2], band[-2:], band[:, :2], band[:, -2:] = True, True, True, True
        edge = set(np.unique(labels[band & solid])) - {0}  # real pixels at the border, not the grown blob
        keep = np.isin(labels, [k for k in range(1, n + 1) if k == main_label or k not in edge])
        out[..., 3] = np.where(ndimage.binary_dilation(keep, iterations=2), out[..., 3], 0)
    return out


def cells(rgba: np.ndarray, rows: int, cols: int, bleed: int) -> list[np.ndarray]:
    h, w = rgba.shape[:2]
    out = []
    for r in range(rows):
        for c in range(cols):
            y0, y1 = max(0, r * h // rows - bleed), min(h, (r + 1) * h // rows + bleed)
            x0, x1 = max(0, c * w // cols - bleed), min(w, (c + 1) * w // cols + bleed)
            out.append(main_blob(rgba[y0:y1, x0:x1]))
    return out


def square_icon(rgba: np.ndarray, size: int, fill: float) -> Image.Image:
    ys, xs = np.nonzero(rgba[..., 3] > 8)
    crop = Image.fromarray(rgba[ys.min():ys.max() + 1, xs.min():xs.max() + 1], "RGBA")
    k = size * fill / max(crop.size)
    crop = resize_rgba(crop, (max(1, round(crop.width * k)), max(1, round(crop.height * k))))
    icon = Image.new("RGBA", (size, size))
    icon.alpha_composite(crop, ((size - crop.width) // 2, (size - crop.height) // 2))
    return icon


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheet", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--grid", required=True, help="RxC, e.g. 2x3")
    ap.add_argument("--names", nargs="+", required=True)
    ap.add_argument("--key", choices=["auto", "blue", "green"], default="auto")
    ap.add_argument("--bleed", type=int, default=0)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--fill", type=float, default=0.85)
    args = ap.parse_args()

    rows, cols = (int(v) for v in args.grid.lower().split("x"))
    if len(args.names) != rows * cols:
        raise SystemExit(f"--names has {len(args.names)} entries for a {rows}x{cols} grid")
    rgba = key_out(np.array(Image.open(args.sheet).convert("RGB")), args.key)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, cell in zip(args.names, cells(rgba, rows, cols, args.bleed)):
        if name == "-":
            continue
        if not (cell[..., 3] > 8).any():
            print(f"{name}: empty cell, skipped")
            continue
        square_icon(cell, args.size, args.fill).save(args.out / f"{name}.png")
        right_edge = int((cell[:, -1, 3] > 8).sum())
        warn = "  <- touches the cell edge: try a larger --bleed" if right_edge > 4 else ""
        print(f"{name}{warn}")


if __name__ == "__main__":
    main()
