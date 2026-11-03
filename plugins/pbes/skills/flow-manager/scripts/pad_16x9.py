"""Put a character master on a 16:9 chroma canvas, ready to be a video's first frame.

    python pad_16x9.py master.jpg out_16x9.png [--fill 0.86] [--height 1024] [--key auto|blue|green]

Video models crop a square master. The character is keyed out, scaled to --fill of the height (leave room for
tails, flames, hair) and centred on a flat background of the same key color. If uploads are not possible in your
setup, ask Flow itself for this edit instead (see references/flow-ui.md) and check the fill it produced.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from chroma import detect_key, key_out

FLAT = {"green": (0x00, 0xB1, 0x40), "blue": (0x00, 0x00, 0xFF)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--fill", type=float, default=0.86)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--key", choices=["auto", "blue", "green"], default="auto")
    args = ap.parse_args()

    rgb = np.array(Image.open(args.src).convert("RGB"))
    key = detect_key(rgb) if args.key == "auto" else args.key
    sprite = Image.fromarray(key_out(rgb, key), "RGBA")
    sprite = sprite.crop(sprite.getbbox())
    h = args.height
    w = round(h * 16 / 9)
    target_h = round(h * args.fill)
    sprite = sprite.resize((round(sprite.width * target_h / sprite.height), target_h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), FLAT[key])
    canvas.paste(sprite, ((w - sprite.width) // 2, (h - target_h) // 2), sprite)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.out)
    print(f"{args.out} {w}x{h}, character {sprite.width}x{target_h}")


if __name__ == "__main__":
    main()
