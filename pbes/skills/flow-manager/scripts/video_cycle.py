"""Find a seamless loop in video frames (e.g. a walk in place) and sample N evenly spaced frames from it.

    ffmpeg -i walk.mp4 frames/f_%03d.png          # extract first (ffmpeg must be installed)
    python video_cycle.py frames/ cycle/ [--frames 8] [--prefix walk] [--start-min 8]
                          [--period-min 14] [--period-max 40]

Searches the (start, period) pair whose last frame best matches the first one (mean difference of small greyscale
thumbnails): that is where the cycle closes without a jump. Skips the first --start-min frames (video models often
ease in). Prints start, period and loop_diff; compare loop_diff with an approved cycle when you have one (lower is
smoother; above ~3 the loop will visibly jump).
"""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

THUMB = (96, 96)


def frame_diff(a: Image.Image, b: Image.Image) -> float:
    return ImageStat.Stat(ImageChops.difference(a, b)).mean[0]


def best_loop(thumbs: list[Image.Image], start_min: int, pmin: int, pmax: int) -> tuple[int, int, float]:
    best = (start_min, pmin, float("inf"))
    for start in range(start_min, len(thumbs) - pmin):
        for period in range(pmin, min(pmax, len(thumbs) - start - 1) + 1):
            d = frame_diff(thumbs[start], thumbs[start + period])
            if d < best[2]:
                best = (start, period, d)
    return best


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--prefix", default="walk")
    ap.add_argument("--start-min", type=int, default=8)
    ap.add_argument("--period-min", type=int, default=14)
    ap.add_argument("--period-max", type=int, default=40)
    args = ap.parse_args()

    paths = sorted(args.src.glob("*.png"))
    if len(paths) < args.start_min + args.period_min + 1:
        raise SystemExit(f"only {len(paths)} frames in {args.src}: not enough for a loop search")
    thumbs = [Image.open(p).convert("L").resize(THUMB) for p in paths]
    start, period, diff = best_loop(thumbs, args.start_min, args.period_min, args.period_max)
    picks = [start + round(i * period / args.frames) for i in range(args.frames)]
    args.out.mkdir(parents=True, exist_ok=True)
    for i, idx in enumerate(picks, 1):
        Image.open(paths[idx]).save(args.out / f"{args.prefix}_{i}.png")
    print(json.dumps({"start": start, "period": period, "loop_diff": round(diff, 2),
                      "picked": [paths[i].name for i in picks]}))


if __name__ == "__main__":
    main()
