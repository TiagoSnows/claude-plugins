"""Copy a Google Flow download into the project's art sources and write its provenance next to it.

    python flow_import.py <download> <dest> --url <flow item URL> --prompt-file prompt.txt
                          [--model "Nano Banana 2.1"] [--refs ref1.png ref2.jpg] [--usage usage.json]
                          [--note "why this attempt was chosen / what was discarded"]

Writes <dest>.json with: tool, model, flow_url, date, prompt (store it WITHOUT the "Generate an image (do not
rewrite...)" opener), refs (project-relative paths of the reference images), download_name, sha256 of the copied
file, an optional "usage" block (frames, fps, loop, in-game size: whatever the project's integration needs) and an
optional free-text note. The sha256 is what makes the provenance verifiable: never edit the copied file afterwards;
retouch derived files (cut icons, frames) instead and say so in the note.
"""
import argparse
import hashlib
import json
import shutil
from datetime import date
from pathlib import Path


def provenance(src: Path, dest: Path, url: str, prompt: str, model: str, refs: list[str],
               usage: dict | None = None, note: str = "") -> dict:
    meta = {
        "tool": "Google Flow",
        "model": model,
        "flow_url": url,
        "date": date.today().isoformat(),
        "prompt": prompt.strip(),
        "refs": refs,
        "download_name": src.name,
        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
    }
    if usage:
        meta["usage"] = usage
    if note:
        meta["note"] = note
    return meta


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("src", type=Path)
    ap.add_argument("dest", type=Path)
    ap.add_argument("--url", required=True)
    ap.add_argument("--prompt-file", type=Path, required=True)
    ap.add_argument("--model", default="Nano Banana 2.1")
    ap.add_argument("--refs", nargs="*", default=[])
    ap.add_argument("--usage", type=Path, help="JSON file with the integration block")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    if args.dest.exists():
        raise SystemExit(f"{args.dest} already exists: import under a new name (e.g. _v2) instead of overwriting")
    args.dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.src, args.dest)
    usage = json.loads(args.usage.read_text(encoding="utf-8")) if args.usage else None
    meta = provenance(args.src, args.dest, args.url, args.prompt_file.read_text(encoding="utf-8"), args.model,
                      args.refs, usage, args.note)
    Path(f"{args.dest}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(args.dest)


if __name__ == "__main__":
    main()
