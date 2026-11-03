# `.flow-manager.json` (project root)

Per-project settings, so the skill stays generic. Create it on first use: fill what you can discover from the repo
(art folders, existing provenance files, commit style, cleanup scripts) and ask the user only for the rest
(usually the Flow project URL). Show it to the user once written.

| Field | Meaning |
|---|---|
| `flow_project_url` | the Flow project where generations happen and references live |
| `art_root` | where approved source art and its provenance live (committed) |
| `scratch_dir` | where downloads (`<run>/dl<N>/`), cuts and boards go before approval (not committed; may be a session temp dir). Pick a layout the `cleanup` command actually reaches, or the downloads pile up |
| `default_image_model` | e.g. `Nano Banana 2.1`; `quality_fallback_model` for when it drifts from the approved look and quota allows |
| `style_sentence` | the art-style sentence every character/animation prompt repeats verbatim |
| `icon_style_sentence` | the style sentence for icons, when it differs from the characters' (it usually does: icons add a highlight and a comic burst) |
| `reserved_colors` | colors with gameplay meaning, forbidden elsewhere (e.g. `{"magenta": "danger only"}`) |
| `molds` | approved provenance JSONs by piece type (icon sheet, effect, master, pose sheet, walk video) |
| `review_ground` | RGB of the neutral ground for boards (close to the app's ground) |
| `icon_check_px` | the size icons are judged at (as small as they appear in the app) |
| `integration` | the project's own commands after approval (atlas/effects/icon build, engine import, tests) |
| `commit_art` | commit message convention for approved art |
| `cleanup` | command that deletes downloads/captures after approval |
| `report_language` | language for briefs, reports and questions |
| `notes` | anything else agents must know (e.g. "references live under All, not Uploads") |

Example (from the game where this workflow was developed):

```json
{
  "flow_project_url": "https://flow.google.com/project/<your-project-id>",
  "art_root": "assets-src",
  "scratch_dir": "<session scratchpad>",
  "default_image_model": "Nano Banana 2.1",
  "quality_fallback_model": "Nano Banana Pro",
  "style_sentence": "2D anime cel shading, bold warm dark-plum outline of constant thickness, flat colors with exactly one hard-edged shadow tone, light from the upper left, subtle cool rim light on the right edge",
  "reserved_colors": {"magenta": "enemy danger only", "cyan": "boss", "gold": "elite"},
  "molds": {
    "icon_sheet": "assets-src/ui/icones/fonte/armas_heroi_f7.jpg.json",
    "effect_loop": "assets-src/fx/incenso/folha.jpg.json",
    "master_edit": "assets-src/heroes/ninja-raposa/manto/mestre_manto_v2.jpg.json",
    "pose_sheet": "assets-src/heroes/ninja-raposa/manto/esfera-espiral/folha_v2.jpg.json",
    "walk_video": "assets-src/heroes/ninja-raposa/manto/andar/andar_v2.mp4.json"
  },
  "review_ground": [196, 190, 168],
  "icon_check_px": 70,
  "integration": [
    "py -I pipeline/build/build_ui_art.py assets-src/ui game/assets --key-art key_art_v3.jpg",
    "py -I pipeline/build/build_fx.py pipeline/build/fx.json",
    "py -I pipeline/build/build_hero.py pipeline/build/heroes/<hero>.json",
    "bash tools/godot-net.sh --headless --path game --import",
    "bash tools/test.sh"
  ],
  "commit_art": "feat(arte): <what> (<model>)",
  "cleanup": "bash tools/limpar-capturas.sh",
  "report_language": "pt-BR",
  "notes": "Never mention AI in commits. Masters are in Flow under 'All' (Tudo)."
}
```
