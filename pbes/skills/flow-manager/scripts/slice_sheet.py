"""Slice a character pose sheet (chroma green/blue or black background) into frames, splitting poses by gaps.

    python slice_sheet.py <sheet> <out_dir> --rows 2 [--prefix attack] [--bg auto|green|blue|black]
                          [--min-gap 20] [--pad 8]

Image models do not keep a rigid grid (a stretched punch crosses into the next cell), so each row is split where
there are columns with no subject pixel. Pieces narrower than 6% of the width (loose sparks, speed lines) are
merged into the nearest neighbour. Frames keep the full row height, preserving the ground line, and stay RGB
with the background as delivered (the game pipeline keys them later), named <prefix>_1..N.png.
If a pose from the bottom row reaches into the top row (hair, ears, flames), a fixed row cut breaks it: ask
for more vertical margin in the prompt, or slice that sheet by hand.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
from chroma import black_out, detect_key, key_out

MIN_POSE_WIDTH_PCT = 6.0


def subject_mask(rgb: np.ndarray, bg: str) -> np.ndarray:
    if bg == "black":
        mask = black_out(rgb)
    else:
        mask = key_out(rgb, detect_key(rgb) if bg == "auto" else bg)[..., 3] > 128
    return ndimage.median_filter(mask.astype(np.uint8), size=5) > 0  # drop JPEG speckles


def column_segments(mask: np.ndarray, min_gap: int) -> list[tuple[int, int]]:
    filled = list(mask.any(axis=0)) + [False] * (min_gap + 1)
    segments, start, gap = [], None, 0
    for x, on in enumerate(filled):
        if on:
            start = x if start is None else start
            gap = 0
        elif start is not None:
            gap += 1
            if gap > min_gap:
                segments.append((start, x - gap + 1))
                start, gap = None, 0
    return segments


def merge_small(segments: list[tuple[int, int]], min_width: int) -> list[tuple[int, int]]:
    merged = list(segments)
    while len(merged) > 1:
        small = [i for i, (a, b) in enumerate(merged) if b - a < min_width]
        if not small:
            break
        i = small[0]
        a, b = merged.pop(i)
        if i == 0:
            j = 0
        elif i == len(merged):
            j = i - 1
        else:
            j = i - 1 if a - merged[i - 1][1] <= merged[i][0] - b else i
        na, nb = merged[j]
        merged[j] = (min(a, na), max(b, nb))
    return merged


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheet", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--rows", type=int, required=True)
    ap.add_argument("--prefix", default="frame")
    ap.add_argument("--bg", choices=["auto", "green", "blue", "black"], default="auto")
    ap.add_argument("--min-gap", type=int, default=20)
    ap.add_argument("--pad", type=int, default=8)
    args = ap.parse_args()

    sheet = Image.open(args.sheet).convert("RGB")
    rgb = np.array(sheet)
    h, w = rgb.shape[:2]
    row_h = h // args.rows
    args.out.mkdir(parents=True, exist_ok=True)
    n = 0
    for r in range(args.rows):
        mask = subject_mask(rgb[r * row_h:(r + 1) * row_h], args.bg)
        segs = merge_small(column_segments(mask, args.min_gap), round(w * MIN_POSE_WIDTH_PCT / 100))
        for a, b in segs:
            n += 1
            box = (max(0, a - args.pad), r * row_h, min(w, b + args.pad), (r + 1) * row_h)
            sheet.crop(box).save(args.out / f"{args.prefix}_{n}.png")
        print(f"row {r + 1}: {len(segs)} poses {segs}")
    print(f"{n} frames -> {args.out}")


if __name__ == "__main__":
    main()
