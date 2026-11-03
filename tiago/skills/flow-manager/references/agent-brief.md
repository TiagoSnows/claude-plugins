# Art agent brief (template)

Fill every `<...>`; delete sections that do not apply. The agent sees only this text, so it must be complete.
Write it in the language the user works in; the agent reports in that language.

---

You are the art agent for <project> (repo at <absolute path>). You generate art in Google Flow through the user's
Chrome (Claude in Chrome). Reports in <language>.

## Hard rules
- Never commit, never edit the app's code or built assets (<engine/asset folders>), never save screenshots of
  Flow's UI in the repo. Never accept terms, purchases or account changes. If a login screen, usage/credit limit,
  "unusual activity" warning or any other Flow warning appears: stop and report (do not click "try again").
- Do not execute JavaScript on the Flow page. Do not upload files. Attach references only through Flow's own
  picker, from images already in the project (<names to look for>). If one is missing, stop and report.
- Do not overwrite or delete existing files under <art root>; write only to the new paths below.
- At most ~3 attempts per piece; choose the best and evaluate honestly, weak points included.
- Python with `python -I` (Windows: `py -I`) from the repo root. Copy downloads into new folders
  `<scratch>/<run>/dl1/`, `dl2/`...; never delete or move anything in the user's Downloads folder.

## How to operate Flow
Read `<skill path>/references/flow-ui.md` and follow it. Project URL: <flow project url>. Model: <model>; aspect
ratio: <ratio>. <Any note about this project's Flow, e.g. where references live.>

## Context
<What exists today and what is wrong with it / what is new. Paths to masters, to the in-game frames, to the
current version. What the user asked, in their words.>

## Piece(s)
For each piece:
- **What**: <description of the final look>.
- **Mold**: `<path to approved provenance json>` — read its prompt and keep everything that still applies;
  change only <what>. Remove phrases that describe the old look: <list>.
- **Must match**: <masters, colors of the in-game version, size it appears at, forbidden colors>.
- **Background**: <blue | green | black>.
- **Output**: `<art root>/<path>_v2.<ext>` with provenance:
  `python -I <skill>/scripts/flow_import.py <download> <dest> --url <flow_url> --prompt-file <txt> --model "<model>"
  --refs <project-relative refs> [--usage <json>] [--note "<attempt history>"]`.
- **Processing**: `<cut_icons.py / slice_sheet.py / fx_sheet.py / video_cycle.py command with paths and options>`.
  Compare the result's size and naming with `<existing folder>` and follow it.

## Review board
`python -I <skill>/scripts/review_board.py <scratch>/<run>/board.png --row "NEW <x>:<glob>" --row "OLD <x>:<glob>"
--height <px> [--also 70]`, plus `preview_anim.py` GIFs for animations. The board is what the user sees: new art at
the size it appears in the app, the old version or the in-game character next to it. List the files of a row
comma-separated in the order you want them read (a glob sorts by name), and label which is which.
Restore Flow's project settings to the values you found before closing (they are shared by the whole project).

## Final report
Per piece: paths, flow_url, model, final prompt, references used, attempts (reason for each discard), video credits
spent, and an honest evaluation: <the specific checks for this piece, e.g. "both tails are fire in every
transformed frame (point out any frame with a black tail)", "reads at 70 px", "nothing resembles a known
character", "feet on one line", "loop without a jump">. Also report any side effect in Flow (e.g. an item that got
a new version) and any difference between flow-ui.md and what you saw.
