"""Build the review board the user approves from: labelled rows of images over a neutral ground, at reading sizes.

    python review_board.py board.png --row "NEW walk:frames_v2/*.png" --row "OLD walk:frames/*.png"
                           [--height 160] [--also 70] [--ground 196,190,168] [--key auto|blue|green|none]

Each --row is "label:glob" (or "label:a.png,b.png"). Every image is keyed (chroma backgrounds), cropped to its
content and drawn at --height px tall; --also adds a second, smaller copy of each image right after it (icons are
judged at the size they appear in the game, e.g. 70 px). Put the old version under the new one when replacing art,
and a frame of the in-game character next to a portrait or icon, so the user compares instead of guessing.
Keep boards small (they are what the user looks at, not the raw downloads).
"""
import argparse
import glob
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from chroma import key_out, resize_rgba

GAP = 12
LABEL_H = 22


def load(path: str, key: str) -> Image.Image:
    im = Image.open(path)
    if key == "none" or (im.mode == "RGBA" and np.array(im)[..., 3].min() < 255):
        im = im.convert("RGBA")
    else:
        im = Image.fromarray(key_out(np.array(im.convert("RGB")), key), "RGBA")
    box = im.getbbox()
    return im.crop(box) if box else im


def scaled(im: Image.Image, height: int) -> Image.Image:
    return resize_rgba(im, (max(1, round(im.width * height / im.height)), height))


def expand(spec: str) -> tuple[str, list[str]]:
    label, _, files = spec.partition(":")
    paths = []
    for part in files.split(","):
        hits = sorted(glob.glob(part.strip()))
        paths += hits if hits else [part.strip()]
    return label, paths


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", type=Path)
    ap.add_argument("--row", action="append", required=True)
    ap.add_argument("--height", type=int, default=160)
    ap.add_argument("--also", type=int, default=0, help="second, smaller copy of each image (e.g. 70 for icons)")
    ap.add_argument("--ground", default="196,190,168")
    ap.add_argument("--key", choices=["auto", "blue", "green", "none"], default="auto")
    args = ap.parse_args()

    ground = tuple(int(v) for v in args.ground.split(","))
    rows = []
    for spec in args.row:
        label, paths = expand(spec)
        tiles = []
        for p in paths:
            im = load(p, args.key)
            tiles.append(scaled(im, args.height))
            if args.also:
                tiles.append(scaled(im, args.also))
        rows.append((label, tiles))
    width = max(sum(t.width + GAP for t in tiles) + GAP for _, tiles in rows)
    height = sum(LABEL_H + args.height + GAP for _ in rows) + GAP
    board = Image.new("RGBA", (width, height), ground + (255,))
    draw = ImageDraw.Draw(board)
    y = GAP
    for label, tiles in rows:
        draw.text((GAP, y), label, fill=(40, 30, 40, 255))
        x = GAP
        for t in tiles:
            board.alpha_composite(t, (x, y + LABEL_H + args.height - t.height))
            x += t.width + GAP
        y += LABEL_H + args.height + GAP
    args.out.parent.mkdir(parents=True, exist_ok=True)
    board.convert("RGB").save(args.out)
    print(f"{args.out} {width}x{height}")


if __name__ == "__main__":
    main()
