# Prompting Flow for production art

## Contents
1. Principles
2. Backgrounds and keys
3. Skeletons: icon sheet · effect loop · character master · edit of a master · pose/action sheet · walk/idle video ·
   16:9 frame for video
4. Consistency across frames and pieces
5. Look-alikes and text
6. When a prompt fails

## 1. Principles

- **Start from a mold.** An approved prompt (in the provenance JSON of a similar piece) already encodes the style,
  the outline, the layout tricks and the fixes from earlier failures. Copy it; change only the subject. Write down
  in the provenance note which earlier attempts were discarded and why (with their flow_url) — that history is what
  makes the next mold better.
- **Say the layout in numbers.** "EXACTLY 4 frames in a grid of EXACTLY 2 rows x 2 columns (two in the top row, two
  in the bottom row, nothing else)". Models add a 5th or 7th pose when the count is only implied.
- **Margins are the cutting script's lifeline.** Ask for every object centred in its own cell with wide empty space,
  never touching the cell border or the image edge. Tall parts (ears, flames, hats, tails) are what cross borders.
- **Describe the art style the same way every time.** For a cel look that worked: "2D anime cel shading, bold warm
  dark-plum outline of constant thickness, flat colors with exactly one hard-edged shadow tone, light from the upper
  left". Change the project's style sentence in the config, then reuse it verbatim.
- **Reserve gameplay colors.** If a color means something in the app (e.g. magenta = danger), forbid it explicitly
  in every other piece ("NO magenta, NO pink").

## 2. Backgrounds and keys

| Piece contains | Background | Cut with |
|---|---|---|
| green (foliage, jade), no blue | flat pure BLUE #0000FF | `cut_icons.py --key blue` |
| blue/cyan (clothes, water, energy) | flat chroma GREEN #00b140 | `--key green` (and forbid green in the subject) |
| glowing effects (fire, energy, smoke) | flat pure BLACK #000000 | `fx_sheet.py` |
| characters for animation | flat chroma GREEN #00b140, "no floor, no shadow" | `slice_sheet.py` / engine pipeline |

Always add: "no grid lines, no cell borders, no frames, no text". Flow never returns the exact hex: #00b140 comes
back as roughly (5,175,68) and #0000FF as roughly (0,70,255); the scripts detect and handle both.

Icon and effect colors must match the in-game version of the same thing. If the icon must avoid the key color
(a blue ball on a blue background), switch the background, do not change the object's color.

## 3. Skeletons

Replace `<...>`. Keep the capitalised words: they are what the model obeys.

**Icon sheet** (1:1, blue or green):
> SQUARE 1:1 image. Sheet of GAME ICONS for the level-up cards and HUD of <genre> game, in a grid of <R> rows x <C>
> columns, each icon centered in its own square cell with wide empty space between icons, all icons the same size.
> Each icon is ONE single object or symbol, centered, big and simple so it reads even at 70 pixels: <style
> sentence>; saturated colors. <optional: behind each object a small jagged comic BURST shape in pale yellow and
> white>. All ORIGINAL designs: nothing recognizable from any existing series, no logos, no letters, no numbers, no
> writing, no text. NO <forbidden colors> in the icons. Solid flat pure <BLUE #0000FF | chroma GREEN #00B140>
> background everywhere, no grid lines, no cell borders, no frames. Top row, left to right: (1) <NAME>: <one
> object, materials, colors>. (2) ... Exactly <N> icons, no duplicates, every icon fully inside its cell with a
> margin, nothing cut off by the image edges.

Portrait icons (busts) use the same skeleton with "head-and-shoulders bust, facing front with a slight 3/4 turn" and
a precise description of each character taken from their masters.

**Effect loop** (16:9 or 1:1, black):
> 2D anime game VISUAL EFFECT sprite sheet, cel-shaded FX style: <EFFECT>. Colors: <palette> only (NO <forbidden>).
> EXACTLY <N> frames in a grid of EXACTLY <R> rows x <C> columns (<describe the rows>), read left to right, top row
> first, each effect centered in its own cell with a lot of empty space around it, never touching the cell borders.
> It is a seamless LOOP of <what>, the same size in every frame; from frame to frame <what moves>. READABILITY RULE:
> the effect is shown with normal transparency over a LIGHT ground, so build it only from bright, fully saturated
> color shapes: a white or pale core, a solid band of saturated color around it and a thin bright saturated outer
> edge. NO dark tones, NO dark outlines, NO soft faint haze or large dim glow (dim areas become invisible). Flat cel
> shapes with crisp hard-edged color steps. Solid pure flat BLACK #000000 background everywhere, no gradient, no
> floor, no text, no grid lines, no characters.

Ask for "NOT a spiral and NOT a vortex" when the effect must not resemble another one, and for a size ("about 60
percent of the cell width") when the first attempt comes out tiny or touching the borders.

**Character master** (1:1, green): one full-body character, relaxed standing pose, three-quarter view facing right,
"Exactly one character, centered, the whole body fully visible with an even empty margin", outfit described piece
by piece, style sentence, background sentence. Masters are the reference for everything else: get them approved
before any animation.

**Edit of a master** (attach the master as Image 1):
> Edit Image 1. Keep EXACTLY the same character, same pose, same <view>, same framing, same scale and position in the
> canvas, same face, <list the identity details>, same outline and same shading as Image 1. Change only ONE thing:
> <the change, described as the final look, matching an existing part when possible ("in exactly the same style,
> color and finish as the <part> that already exists")>. <What must stay untouched>. <background sentence>.

Edits are the cheapest way to fix one detail across a character. Compare old and new pixel by pixel outside the
edited area to confirm nothing else moved.

**Pose / action sheet** (16:9, green; attach the master as Image 1):
> Game sprite sheet of the character in Image 1 <doing what>. <N> frames in a grid of <R> rows x <C> columns, read
> left to right, top row first. Keep the SAME character exactly as in Image 1 (<identity details>). Use the same
> head-to-body ratio as Image 1 (about <k> heads tall), the same character scale in every frame, and the same
> three-quarter view turned to the RIGHT, never facing the camera. <style sentence>. Feet on the same ground line in
> each row. Frame 1: <pose>. Frame 2: ... Do NOT draw speed lines, impact frames, radiating lines, shockwave rings,
> big dust clouds or any effect background inside the cells; only effects attached to his body are allowed, and
> short motion arcs right next to a moving limb. Every pose fits entirely inside its own cell with a clear empty
> margin on all four sides. <background sentence>.

Describe every frame; leave big impact effects to separate effect sheets (they are drawn by the engine).

**Walk / idle cycle** (video from a 16:9 first frame):
> Generate a video with <video model> using the attached image as the first frame (do not rewrite or shorten these
> instructions). 2D anime cel-shaded game sprite animation. The <character> from the first frame walks IN PLACE in a
> light, quick walk cycle, staying exactly in the center of the frame and never travelling sideways. Facing right in
> the same three-quarter view the whole time, no turning toward the camera. The legs clearly ALTERNATE every step,
> the arms swing opposite to the legs, with a small up-and-down rhythmic bob. <parts that flicker/trail>. Static
> locked camera: no pan, no zoom, no rotation. The full body stays fully visible inside the frame at all times.
> Same character design, colors, and art style with bold outlines. Solid flat chroma green background the whole
> time, no floor, no shadow, no other objects, no text.

Then: ffmpeg frames → `video_cycle.py` → compare `loop_diff` with the previous cycle → `preview_anim.py`.

**16:9 first frame for video**: either `pad_16x9.py --fill 0.86` (needs an upload the user does) or ask Flow to edit
the master onto a 16:9 green canvas "occupying about 85% of the height, centered". Check the fill afterwards: Flow
tends to fill ~95%, which leaves tails or hair touching the top in the video.

## 4. Consistency

- Every animation of a character uses its approved master as Image 1. When the master changes, every animation that
  shows the changed part must be regenerated from the new master; list them before starting.
- Remove from old molds any phrase that describes the old look (e.g. an accessory that no longer exists), or the
  model brings it back. Replace it with a precise description of what stays ("a plain short black scarf around
  his neck") rather than a blanket "NO scarf", which deletes the part entirely. Frames that show the character
  before a transformation keep the normal outfit.
- Game engines usually normalize each animation's height from a reference frame. A crouched first frame inflates
  the scale; prefer a standing frame as the reference and say so when integrating.

## 5. Look-alikes and text

- Archetypes collide with famous characters (straw hat + scar under the eye; golden spiky hair with an aura).
  Forbid the telltale detail explicitly ("NO scar, NO stitches, NO marks under the eyes"; "short hair that only
  lifts a little, NO tall stiff spikes") and check faces at zoom. A tiny leftover mark can be retouched on the
  derived icon instead of spending another generation.
- Asking for labels, names or "captions" makes Flow write them in the image. Never name the pieces in a way that
  reads like a caption; describe them.

## 6. When a prompt fails

- Same failure twice → change the prompt's structure (layout sentence, size, background), not just add adjectives.
- A detail that keeps drifting → do it as an edit of an approved image instead of a fresh generation.
- Wrong count / extra pose → restate "EXACTLY N" and describe each row.
- Halo or cut edges after cutting → that is the script's job (`--key`, `--bleed`), not a reason to regenerate.
