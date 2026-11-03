---
name: flow-manager
description: Produce game/app art in Google Flow (Nano Banana image models, Omni/Veo video) on the user's behalf through their own Chrome, so the user only approves review boards. The session writes the brief, a background art agent drives Flow, approved art is imported with provenance and processed (chroma key, icon cuts, pose sheets, effect frames, walk-cycle loops from video) and integrated. Use this whenever the user wants new art, icons, sprites, character masters, poses, effects, animations or a short video generated in Google Flow, wants generated art redone or fixed (recolor, missing detail, different pose, look-alike problems), or types /flow-manager — even if they only say "gera no Flow", "faz a arte disso", "refaz esse ícone" or "make the sprite for this".
compatibility: Claude in Chrome connected to the user's Chrome, signed into Google Flow with an existing project; the Agent tool (background subagents); Python 3.10+ with Pillow, numpy and scipy; ffmpeg only for video work.
---

# Flow Manager

The user's time goes into judging art, not into operating Google Flow. This skill splits the work so that is what
happens:

- **You (main session)** turn the request into a precise brief, launch the art agent, review what comes back,
  show the user a small review board, and handle everything after approval (import, processing, integration,
  commit, cleanup). You do not touch the Chrome browser while an art agent is working in it.
- **The art agent** (a background subagent) drives Flow in the user's Chrome: types prompts, attaches references
  that already live in the Flow project, downloads results, records provenance, runs the cutting scripts and builds
  the review board. It never commits and never edits the app's code or built assets.
- **The user** approves or asks for changes at each gate. Nothing generated reaches the project's history without
  that approval.

This loop worked over dozens of pieces (characters, animations, effects, icons) because each role does only what it
is good at, and because every decision the user makes is made from a board that shows the new art at the size it
will be seen, next to what it replaces.

## 1. Project setup (first use in a project)

Look for `.flow-manager.json` at the project root. If it is missing, ask the user only what you cannot find in the
repo (usually the Flow project URL), then write it. Fields and an example are in `references/config.md`. The config
says where approved art lives, where downloads and scratch files go, the default model, the review ground color,
the commit convention and where the approved "molds" (previous provenance files) are.

## 2. From request to brief

1. **Classify the piece**: icon sheet, visual effect loop, character master, edit of an existing master, pose /
   action sheet, walk or idle cycle (video), 16:9 frame for video, prop sheet. `references/prompting.md` has the
   rules and a prompt skeleton for each.
2. **Find a mold**: an approved provenance JSON of the same kind of piece (`<file>.json` next to approved art).
   Reusing a prompt that already passed the user's eye is the single biggest quality lever: copy it and change only
   what the new piece needs. Say which mold you used.
3. **Check what the new piece must match**: masters of the character, the size it appears at, colors reserved for
   gameplay meaning (e.g. a "danger" color), the background color the cutting script needs (blue for things that
   contain green, green for things that contain blue, black for glowing effects).
4. **Write the brief** from `references/agent-brief.md`. It must be self-contained: the agent knows nothing of this
   conversation. Include the exact output paths (new names such as `_v2`, never overwriting approved files), the
   cutting command, what the review board must show, and the hard rules below.
5. **Launch** it with the Agent tool in the background (`subagent_type: general-purpose`, a short `name` such as
   `art-icons`), then keep working on other things. Several unrelated pieces can be one agent run (one board), but
   an animation that depends on a master waits for the master's approval. If you cannot launch a background agent
   (no Agent tool, or you are yourself running as a subagent), do the agent's part in this session following
   `references/flow-ui.md`, then come back to the gate below.
6. **Tell the user** in one line that a run started, what it will produce and that files will land in their
   Downloads folder.

## 3. The approval gate

When the agent reports:

1. **Look at the board yourself first** (Read the PNG). Check it against the request and against the agent's own
   list of weak points. If something is clearly broken (wrong grid, cut edges, a halo, text in the image, a
   character that resembles a well-known one), send the agent back once before bothering the user.
2. **Show the user the board** (send the file so it renders) and ask with concrete options: approve; approve with a
   specific small fix you can do yourself (e.g. retouching a derived file); redo a named part. Put the agent's honest
   weak points in the question so the user decides with full information.
3. **Answer questions plainly.** If the user asks something that reveals a mismatch (e.g. "is the ki ball the blue
   one or the yellow one?"), it is a defect of the request, not of the user: fix the inconsistency.
4. **Changes**: resume the same agent with SendMessage (it keeps its context), quoting the user's words.

## 4. After approval

1. **Commit the source art alone**: the downloaded/imported files, their provenance JSONs and the cut results under
   the art root, in their own commit (convention from the config, e.g. `feat(art): <what> (<model>)`). No app code
   in that commit.
2. **Integrate**: run the project's own build steps (atlas, effects manifest, icon copy), re-import in the engine,
   update tests that pin counts or sizes, and **look at it in the running app** (a short capture) before telling the
   user it is done. Size normalization often needs a reference-frame tweak; say what you changed and why.
3. **Clean up**: delete the agent's download/scratch folders and your captures once approved (the config names the
   cleanup command). Never delete anything in the user's Downloads folder or other user files.
4. **Report** in the user's language: what changed, where, what the agent flagged, and any side effect in Flow.

## 5. Hard rules (and why)

- **No JavaScript on the Flow page and no file-input tricks to upload.** Doing that once produced Flow's "unusual
  activity" warning. References are attached only through Flow's own picker, from images already in the project.
  If a reference is not in the project, ask the user to add it.
- **Stop on any Flow warning, login screen, usage/credit limit or terms prompt** and report; never click "try
  again" on a blocked generation, never accept terms, purchases or account changes.
- **At most ~3 attempts per piece.** Pick the best, say honestly what is weak. More attempts cost credits and rarely
  fix a structural prompt problem; rewrite the prompt instead.
- **Never overwrite approved art.** New versions get new names; the provenance sha256 must keep matching its file.
  Retouches go on derived files (cut icons, frames), noted in the provenance `note`.
- **Downloads land in the user's Downloads folder.** Copy them into the scratch folder; leave the originals. Tell
  the user that downloads will happen when a run starts; if they ask about downloads they see, answer exactly which
  ones were yours.
- **Original designs only.** Nothing recognizable from existing series, logos or text. Look-alike details (a scar
  under one eye with a straw hat, tall golden spikes) are a real risk: check every face and point them out.
- **Video costs credits.** Mention it before running a video generation that the user did not explicitly ask for.

## 6. References

- `references/flow-ui.md` — operating Flow's UI step by step (for the agent): settings, prompting, waiting,
  downloading, attaching references, versions, known failures and workarounds.
- `references/prompting.md` — prompt rules and skeletons per piece type, backgrounds, readability rules for effects,
  consistency across frames, video loops, look-alike avoidance.
- `references/agent-brief.md` — the brief template to fill in for the art agent.
- `references/config.md` — `.flow-manager.json` fields and an example.
- `references/pipeline.md` — the bundled scripts and when to use each.

## 7. Bundled scripts (`scripts/`)

Run them with `python -I` (or `py -I` on Windows) from the project root. Tests: `python -m unittest discover -s
<skill>/scripts/tests`.

If the project already has its own art pipeline, use it for what it covers (consistency with the art already
there), except where the bundled script carries a safeguard the project's lacks: `flow_import.py` refuses to
overwrite, `cut_icons.py` keeps detached parts (sparkles, sound waves) and has per-key thresholds. Say which one
you used, and never hand-roll cutting code when a script exists: ad-hoc keying is where green halos come from.

| Script | Use |
|---|---|
| `flow_import.py` | copy a download into the art root and write provenance (refuses to overwrite) |
| `cut_icons.py` | icon sheet on blue/green → square RGBA icons; `--bleed` recovers parts that cross the cell |
| `slice_sheet.py` | pose/action sheet → frames, split by empty columns, full row height |
| `fx_sheet.py` | effect sheet on black → RGBA frames without a dark halo + preview GIF |
| `video_cycle.py` | video frames → seamless loop of N frames |
| `pad_16x9.py` | master → 16:9 chroma canvas for a video's first frame |
| `preview_anim.py` | frames → GIF aligned by the feet, game size + 3x |
| `review_board.py` | labelled rows (new over old) at reading sizes on a neutral ground: what the user approves |
| `chroma.py` | the keying library behind all of the above |
