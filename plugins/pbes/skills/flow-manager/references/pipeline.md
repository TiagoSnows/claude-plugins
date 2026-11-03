# Bundled scripts

All in `<skill>/scripts/`, run with `python -I` (Windows `py -I`) from the project root; each prints what it wrote.
Dependencies: Pillow, numpy, scipy; ffmpeg for video frames. Tests: `python -m unittest discover -s
<skill>/scripts/tests`.

## flow_import.py — provenance
`flow_import.py <download> <dest> --url <flow item URL> --prompt-file p.txt --model "<model>" [--refs ...]
[--usage usage.json] [--note "..."]`
Copies the download and writes `<dest>.json` (tool, model, flow_url, date, prompt, refs, download_name, sha256,
usage, note). Refuses to overwrite: new versions get new names. Put attempt history in `--note` (what was
discarded and why, with flow URLs). `usage` holds what integration needs (frames used, fps, loop, in-game px).

## cut_icons.py — icon sheets
`cut_icons.py <sheet> <out> --grid RxC --names a b - d [--key auto|blue|green] [--bleed N] [--size 256]
[--fill 0.85]`
Keys the background, keeps each cell's main object and every detached part floating inside the cell (sparkles,
sound waves), drops pieces that touch the cell border without being the main object (a neighbour's overflow), and
centres the result on a transparent square. Prints a warning when an icon touches its cell edge: rerun with
`--bleed 40..80` (on a 1024 px sheet) so the part that crossed into the next cell comes back. `-` skips a cell.
Use this script rather than ad-hoc cutting code: its key thresholds and despill are what keep edges clean.

## slice_sheet.py — pose/action sheets
`slice_sheet.py <sheet> <out> --rows R [--prefix name] [--bg auto|green|blue|black] [--min-gap 20] [--pad 8]`
Splits each row at empty columns, merges loose sparks into the nearest pose, keeps the full row height (ground
line) and the original background (engines key it later). If a pose reaches into the next row, the fixed row cut
breaks it; ask for more vertical margin.

## fx_sheet.py — effects on black
`fx_sheet.py <sheet> <out> --cols C --rows R [--prefix fx] [--game-px 96] [--fps 12]`
Black level fix, generator grid lines erased, alpha from the max channel with un-premultiplied color (no dark
halo over light grounds), frames centred in a common box, `preview.gif` over a mid and a light ground.

## video_cycle.py — loops from video
`ffmpeg -i in.mp4 frames/f_%03d.png` then `video_cycle.py frames/ cycle/ --frames 8 [--prefix walk]`.
Prints `loop_diff`; compare with the approved cycle (around 1-1.5 is smooth).

## pad_16x9.py — first frame for video
`pad_16x9.py master.jpg out.png [--fill 0.86]`. Needs the user to add the result to Flow; otherwise ask Flow for
the 16:9 edit and check the fill.

## preview_anim.py — animation check
`preview_anim.py f1.png f2.png ... --out a.gif [--fps 12] [--game-height 112]`. Feet-aligned, game size and 3x.

## review_board.py — what the user approves
`review_board.py board.png --row "NEW x:glob" --row "OLD x:glob" [--height 160] [--also 70]
[--ground 196,190,168]`. Keep it to what decides the approval: new next to old (or next to the in-game character),
at reading size.

## chroma.py — keying library
`key_out(rgb, "auto"|"blue"|"green")`, `detect_key(rgb)`, `black_out(rgb)`. Separate thresholds per key: Flow's
green arrives at ~(5,175,68), far weaker than pure blue, and blue thresholds on it leave a 40% alpha halo.
