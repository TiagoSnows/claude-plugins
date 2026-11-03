"""Chroma keying for Google Flow outputs (blue #0000FF or green #00B140 flat backgrounds).

Library used by the other scripts; also a small CLI that keys a whole image to RGBA:

    python chroma.py <image> <out.png> [--key auto|blue|green]

Why two keys: icons and props that contain green (foliage, jade) go on BLUE; anything that contains blue
(clothes, water, ki energy) goes on GREEN. Flow never returns the exact hex: #00B140 arrives as roughly
(5, 175, 68), whose "greenness" (g - max(r, b)) is ~107, far below pure blue's ~255. That is why each key has
its own thresholds; reusing the blue thresholds for green leaves a ~40% alpha halo around every object.

Alpha is soft between SOLID and CLEAR. The key channel is clamped to the strongest other channel (+10) on every
pixel: prompts forbid the key color in the subject, and JPEG blends it into opaque edge pixels, which turn into a
fringe as soon as the icon is scaled down.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

THRESHOLDS = {  # key strength up to SOLID: opaque; from CLEAR on: transparent
    "blue": (60.0, 140.0),
    "green": (30.0, 80.0),
}
CHANNEL = {"blue": 2, "green": 1}


def strength(rgb: np.ndarray, key: str) -> np.ndarray:
    """How much the key color dominates each pixel: key channel minus the strongest other channel."""
    f = rgb.astype(np.float32)
    k = CHANNEL[key]
    others = [c for c in range(3) if c != k]
    return f[..., k] - np.maximum(f[..., others[0]], f[..., others[1]])


def detect_key(rgb: np.ndarray) -> str:
    """Guess the background from the image border (the subject is asked to keep a margin)."""
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]).astype(np.float32)
    med = np.median(border, axis=0)
    return "blue" if med[2] - max(med[0], med[1]) > med[1] - max(med[0], med[2]) else "green"


def key_out(rgb: np.ndarray, key: str = "auto") -> np.ndarray:
    """RGB (H, W, 3) uint8 -> RGBA uint8 with the flat key background made transparent."""
    if key == "auto":
        key = detect_key(rgb)
    solid, clear = THRESHOLDS[key]
    s = strength(rgb, key)
    alpha = np.clip((clear - s) / (clear - solid), 0.0, 1.0)
    out = rgb.astype(np.float32).copy()
    k = CHANNEL[key]
    others = [c for c in range(3) if c != k]
    cap = np.maximum(out[..., others[0]], out[..., others[1]]) + 10
    out[..., k] = np.minimum(out[..., k], cap)
    return np.dstack([out, alpha * 255]).round().astype(np.uint8)


def resize_rgba(im: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Resize with premultiplied alpha and, when shrinking, a box filter. A plain RGBA resize blends the color of
    transparent pixels (the damped key color) into the edges, and LANCZOS' negative lobes invent colors on low-alpha
    edges; either one brings a green or blue fringe back after a clean key."""
    shrinking = size[0] < im.width or size[1] < im.height
    flt = Image.BOX if shrinking else Image.BICUBIC
    a = np.asarray(im.convert("RGBA"), dtype=np.float32) / 255.0
    alpha = a[..., 3]
    planes = [Image.fromarray(a[..., c] * alpha, "F").resize(size, flt) for c in range(3)]  # premultiplied, float
    new_alpha = np.clip(np.asarray(Image.fromarray(alpha, "F").resize(size, flt)), 0.0, 1.0)
    safe = np.where(new_alpha > 1e-4, new_alpha, 1.0)
    rgb = np.stack([np.clip(np.asarray(p) / safe, 0.0, 1.0) for p in planes], axis=-1)
    out = np.dstack([rgb, new_alpha]) * 255.0
    out[new_alpha <= 1e-4] = 0
    return Image.fromarray(out.round().astype(np.uint8), "RGBA")


def black_out(rgb: np.ndarray, threshold: int = 28) -> np.ndarray:
    """Mask (bool) of non-background pixels for sheets on a black background."""
    return rgb.max(axis=2) >= threshold


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--key", choices=["auto", "blue", "green"], default="auto")
    args = ap.parse_args()
    rgb = np.array(Image.open(args.src).convert("RGB"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(key_out(rgb, args.key), "RGBA").save(args.out)
    print(args.out)


if __name__ == "__main__":
    main()
