"""Animated preview of a frame sequence: keys the background, aligns by the feet and writes a GIF.

    python preview_anim.py f1.png f2.png ... --out cycle.gif [--fps 12] [--game-height 112] [--key auto|blue|green]

Every frame is cropped with one common box anchored on the lowest row (the feet), so bobbing and drifting show up
as they will in the game. The GIF shows the game size (character height in px on screen) next to a 3x version
for detail. Frames that are already RGBA are used as they are.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from chroma import key_out, resize_rgba

BG = (46, 52, 58)


def keyed(path: Path, key: str) -> Image.Image:
    im = Image.open(path)
    if im.mode == "RGBA" and np.array(im)[..., 3].min() < 255:
        return im
    return Image.fromarray(key_out(np.array(im.convert("RGB")), key), "RGBA")


def feet_aligned(frames: list[Image.Image]) -> list[Image.Image]:
    boxes = [f.getbbox() for f in frames]
    box = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
    return [f.crop(box) for f in frames]


def compose(frame: Image.Image, game_h: int) -> Image.Image:
    small = resize_rgba(frame, (max(1, round(frame.width * game_h / frame.height)), game_h))
    big = resize_rgba(frame, (small.width * 3, game_h * 3))
    canvas = Image.new("RGB", (small.width + big.width + 60, big.height + 40), BG)
    canvas.paste(small, (20, canvas.height - 20 - game_h), small)
    canvas.paste(big, (small.width + 40, 20), big)
    return canvas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("frames", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--game-height", type=int, default=112)
    ap.add_argument("--key", choices=["auto", "blue", "green"], default="auto")
    args = ap.parse_args()

    tiles = [compose(f, args.game_height) for f in feet_aligned([keyed(p, args.key) for p in args.frames])]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tiles[0].save(args.out, save_all=True, append_images=tiles[1:], duration=round(1000 / args.fps), loop=0,
                  disposal=2)
    print(f"{len(tiles)} frames -> {args.out}")


if __name__ == "__main__":
    main()
