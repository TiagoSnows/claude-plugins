"""Visual effects on a black background: slice the sheet into RGBA frames without a dark halo, plus a preview GIF.

    python fx_sheet.py <black_bg_sheet> <out_dir> [--cols 2 --rows 2] [--prefix fx] [--game-px 96] [--fps 12]
                       [--threshold 10] [--grid-max 4]

Effects are drawn with normal alpha blending in most engines. Alpha comes from the max channel (a = max(r,g,b))
and color is un-premultiplied (rgb / a), so edges do not darken over a light ground.
1. Black level: generators sometimes return dark grey instead of #000; the 5th percentile is subtracted and the
   rest stretched back to 0-255.
2. Grid lines and frames the generator drew are erased (bands up to --grid-max px lit across >90% of the image).
3. The sheet is split into equal cells (ask for each effect centred in its cell with room around it); every frame
   is the lit content of its cell, centred in a common box so the effect does not drift between frames.
Outputs <prefix>_N.png (RGBA) and preview.gif (each frame over a mid and a light ground, game size and 3x).
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

GROUNDS = {"mid ground": (92, 104, 88), "light ground": (196, 190, 168)}
PAD = 6
ZOOM = 3


def normalize_black(rgb: np.ndarray) -> np.ndarray:
    bg = np.percentile(rgb.reshape(-1, 3), 5, axis=0)
    f = np.clip(rgb.astype(np.float32) - bg, 0, None)
    f *= 255.0 / max(1.0, 255.0 - float(bg.max()))
    return np.clip(f, 0, 255).astype(np.uint8)


def remove_grid_lines(rgb: np.ndarray, threshold: int, max_width: int) -> np.ndarray:
    out = rgb.copy()
    lit = rgb.max(axis=2) > threshold
    for axis in (1, 0):
        idx = np.nonzero(lit.mean(axis=axis) > 0.9)[0]
        for run in np.split(idx, np.nonzero(np.diff(idx) > 1)[0] + 1):
            if 0 < len(run) <= max_width:
                sl = slice(max(0, run[0] - 1), run[-1] + 2)
                if axis == 1:
                    out[sl, :] = 0
                else:
                    out[:, sl] = 0
    return out


def to_rgba(rgb: np.ndarray, threshold: int) -> np.ndarray:
    f = rgb.astype(np.float32)
    a = np.clip((f.max(axis=2) - threshold) / (255.0 - threshold), 0.0, 1.0)
    safe = np.where(a > 0, a, 1.0)[..., None]
    color = np.clip(f / 255.0 / safe, 0.0, 1.0) * 255.0
    out = np.dstack([color, a * 255.0]).round().astype(np.uint8)
    out[a == 0] = 0
    return out


def grid_frames(rgb: np.ndarray, cols: int, rows: int, threshold: int) -> list[np.ndarray]:
    h, w = rgb.shape[:2]
    ch, cw = h // rows, w // cols
    lit = rgb.max(axis=2) > threshold
    half_h = half_w = 1
    for r in range(rows):
        for c in range(cols):
            ys, xs = np.nonzero(lit[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw])
            if len(ys):
                half_h = max(half_h, abs(ys - ch / 2).max())
                half_w = max(half_w, abs(xs - cw / 2).max())
    half_h, half_w = int(half_h) + PAD, int(half_w) + PAD
    frames = []
    for r in range(rows):
        for c in range(cols):
            cy, cx = r * ch + ch // 2, c * cw + cw // 2
            box = np.zeros((2 * half_h, 2 * half_w, 3), np.uint8)
            y0, y1 = max(0, cy - half_h), min(h, cy + half_h)
            x0, x1 = max(0, cx - half_w), min(w, cx + half_w)
            cell = rgb[y0:y1, x0:x1].copy()
            yy, xx = np.mgrid[y0:y1, x0:x1]
            outside = (yy < r * ch) | (yy >= (r + 1) * ch) | (xx < c * cw) | (xx >= (c + 1) * cw)
            cell[outside & lit[y0:y1, x0:x1]] = 0  # what belongs to neighbouring cells
            box[y0 - (cy - half_h):y0 - (cy - half_h) + cell.shape[0],
                x0 - (cx - half_w):x0 - (cx - half_w) + cell.shape[1]] = cell
            frames.append(box)
    return frames


def preview(frames: list[np.ndarray], game_px: int, fps: int, out: Path) -> None:
    scale = game_px / max(frames[0].shape[:2])
    cell = game_px + 16
    big = cell * ZOOM
    width = len(GROUNDS) * (cell + big + 24)
    gif = []
    for f in frames:
        canvas = Image.new("RGB", (width, big + 40), (30, 30, 30))
        d = ImageDraw.Draw(canvas)
        x = 8
        for ground, color in GROUNDS.items():
            d.text((x, 8), ground, fill=(230, 230, 230))
            for size in (cell, big):
                k = scale * size / cell
                tile = np.full((size, size, 3), color, np.float32)
                fr = Image.fromarray(f).resize((max(1, round(f.shape[1] * k)), max(1, round(f.shape[0] * k))),
                                              Image.LANCZOS)
                arr = np.array(fr).astype(np.float32)
                oy, ox = (size - arr.shape[0]) // 2, (size - arr.shape[1]) // 2
                region = tile[oy:oy + arr.shape[0], ox:ox + arr.shape[1]]
                a = arr[..., 3:4] / 255.0
                region[:] = region * (1 - a) + arr[..., :3] * a
                canvas.paste(Image.fromarray(np.clip(tile, 0, 255).astype(np.uint8)), (x, 30))
                x += size + 8
            x += 8
        gif.append(canvas)
    gif[0].save(out, save_all=True, append_images=gif[1:], duration=round(1000 / fps), loop=0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheet", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--rows", type=int, default=2)
    ap.add_argument("--prefix", default="fx")
    ap.add_argument("--game-px", type=int, default=96, help="longest side of a frame in the game, in px")
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--threshold", type=int, default=10)
    ap.add_argument("--grid-max", type=int, default=4, help="widest grid line (px) to erase")
    args = ap.parse_args()

    rgb = normalize_black(np.array(Image.open(args.sheet).convert("RGB")))
    rgb = remove_grid_lines(rgb, args.threshold, args.grid_max)
    args.out.mkdir(parents=True, exist_ok=True)
    frames = []
    for k, crop in enumerate(grid_frames(rgb, args.cols, args.rows, args.threshold), 1):
        rgba = to_rgba(crop, args.threshold)
        Image.fromarray(rgba, "RGBA").save(args.out / f"{args.prefix}_{k}.png")
        frames.append(rgba)
    preview(frames, args.game_px, args.fps, args.out / "preview.gif")
    print(f"{len(frames)} frames {frames[0].shape[1]}x{frames[0].shape[0]} + preview.gif -> {args.out}")


if __name__ == "__main__":
    main()
