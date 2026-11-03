"""Tests for the flow-manager scripts, on synthetic images (no Flow access needed).

    python -m unittest discover -s <skill>/scripts/tests
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import chroma

FLOW_GREEN = (5, 175, 68)  # what #00B140 arrives as
FLOW_BLUE = (0, 70, 255)  # what #0000FF arrives as


def run(script: str, *args) -> str:
    done = subprocess.run([sys.executable, "-I", str(SCRIPTS / script), *map(str, args)],
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(f"{script} failed:\n{done.stderr}")
    return done.stdout


def sheet(bg, shapes, size=(300, 100)) -> Image.Image:
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    for box, color in shapes:
        d.ellipse(box, fill=color)
    return img


class ChromaTest(unittest.TestCase):
    def test_detects_the_background(self):
        self.assertEqual(chroma.detect_key(np.array(sheet(FLOW_GREEN, [((30, 30, 70, 70), (255, 0, 0))]))), "green")
        self.assertEqual(chroma.detect_key(np.array(sheet(FLOW_BLUE, [((30, 30, 70, 70), (0, 200, 0))]))), "blue")

    def test_green_key_has_no_halo_and_keeps_blue_subjects(self):
        rgba = chroma.key_out(np.array(sheet(FLOW_GREEN, [((30, 20, 90, 80), (40, 200, 255))])), "green")
        self.assertEqual(rgba[2, 2, 3], 0, "Flow green is fully transparent")
        self.assertEqual(rgba[50, 60, 3], 255, "blue subject stays opaque")
        semi = (rgba[..., 3] > 0) & (rgba[..., 3] < 250)
        greenish = rgba[..., 1].astype(int) - np.maximum(rgba[..., 0], rgba[..., 2]).astype(int) > 20
        self.assertEqual(int((semi & greenish).sum()), 0, "no green fringe")

    def test_opaque_edge_pixels_lose_their_green_tint(self):
        rgb = np.array(sheet(FLOW_GREEN, [((30, 20, 90, 80), (150, 178, 60))]))  # JPEG-like gold/green edge tone
        rgba = chroma.key_out(rgb, "green").astype(int)
        self.assertEqual(rgba[50, 60, 3], 255, "still opaque")
        self.assertLessEqual(rgba[50, 60, 1] - max(rgba[50, 60, 0], rgba[50, 60, 2]), 10, "key color clamped")

    def test_blue_key_keeps_green_subjects(self):
        rgba = chroma.key_out(np.array(sheet(FLOW_BLUE, [((30, 20, 90, 80), (60, 180, 60))])), "blue")
        self.assertEqual(rgba[2, 2, 3], 0)
        self.assertEqual(rgba[50, 60, 3], 255)


class CutIconsTest(unittest.TestCase):
    def test_grid_cut_and_bleed_recovers_overflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = sheet(FLOW_GREEN, [((20, 20, 80, 80), (250, 250, 250)), ((120, 20, 180, 80), (250, 120, 40)),
                                     ((220, 20, 280, 80), (40, 200, 255))])
            ImageDraw.Draw(img).rectangle((80, 45, 112, 55), fill=(250, 250, 250))  # brim crossing x=100
            path = Path(tmp) / "icons.png"
            img.save(path)
            out = run("cut_icons.py", path, Path(tmp) / "a", "--grid", "1x3", "--names", "one", "two", "-")
            self.assertIn("touches the cell edge", out)
            self.assertFalse((Path(tmp) / "a" / "-.png").exists())
            run("cut_icons.py", path, Path(tmp) / "b", "--grid", "1x3", "--names", "one", "two", "three",
                "--bleed", "20")
            narrow = np.array(Image.open(Path(tmp) / "a" / "one.png"))
            wide = np.array(Image.open(Path(tmp) / "b" / "one.png"))
            ratio = lambda a: np.ptp(np.nonzero(a[..., 3] > 8)[1]) / np.ptp(np.nonzero(a[..., 3] > 8)[0])
            self.assertGreater(ratio(wide), ratio(narrow), "the brim comes back with --bleed")
            self.assertEqual(Image.open(Path(tmp) / "b" / "three.png").size, (256, 256))

    def test_detached_parts_stay_and_neighbour_intrusions_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = sheet(FLOW_GREEN, [((30, 30, 70, 70), (250, 250, 250)), ((130, 30, 170, 70), (250, 120, 40))],
                        size=(200, 100))
            d = ImageDraw.Draw(img)
            d.arc((60, 15, 95, 85), -60, 60, fill=(255, 210, 60), width=5)  # sound wave 20 px away from the speaker
            d.rectangle((90, 0, 99, 6), fill=(250, 120, 40))  # neighbour's part poking into cell 1 at its edge
            path = Path(tmp) / "s.png"
            img.save(path)
            run("cut_icons.py", path, Path(tmp) / "o", "--grid", "1x2", "--names", "one", "two", "--bleed", "0")
            a = np.array(Image.open(Path(tmp) / "o" / "one.png"))
            gold = (a[..., 3] > 200) & (a[..., 0] > 200) & (a[..., 1] > 150) & (a[..., 2] < 120)
            self.assertGreater(int(gold.sum()), 50, "the detached wave is kept")
            orange = (a[..., 3] > 200) & (a[..., 0] > 200) & (a[..., 1] < 150) & (a[..., 2] < 80)
            self.assertEqual(int(orange.sum()), 0, "the neighbour's piece at the cell edge is dropped")

    def test_resized_icons_have_no_green_fringe(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = Image.new("RGB", (1024, 512), FLOW_GREEN)
            d = ImageDraw.Draw(img)
            d.rectangle((150, 190, 330, 320), fill=(245, 245, 240), outline=(58, 18, 48), width=10)
            d.arc((300, 120, 480, 390), -60, 60, fill=(255, 210, 60), width=16)
            path = Path(tmp) / "s.jpg"
            img.save(path, quality=92)
            run("cut_icons.py", path, Path(tmp) / "o", "--grid", "1x2", "--names", "one", "-", "--key", "green")
            a = np.array(Image.open(Path(tmp) / "o" / "one.png")).astype(int)
            vis = a[..., 3] > 8
            semi = vis & (a[..., 3] < 250)
            greenish = (a[..., 1] - np.maximum(a[..., 0], a[..., 2])) > 20
            self.assertLess((semi & greenish).sum() / vis.sum(), 0.002, "resizing must not bring the key color back")

    def test_wrong_name_count_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.png"
            sheet(FLOW_GREEN, [((20, 20, 80, 80), (250, 250, 250))]).save(path)
            with self.assertRaises(AssertionError):
                run("cut_icons.py", path, Path(tmp) / "o", "--grid", "1x3", "--names", "a")


class SliceSheetTest(unittest.TestCase):
    def test_splits_poses_by_gaps_and_merges_sparks(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = Image.new("RGB", (600, 400), FLOW_GREEN)
            d = ImageDraw.Draw(img)
            for row in range(2):
                for x in (40, 240, 440):
                    d.rectangle((x, row * 200 + 30, x + 100, row * 200 + 180), fill=(30, 30, 40))
            d.ellipse((150, 100, 158, 108), fill=(255, 220, 80))  # loose spark next to pose 1
            path = Path(tmp) / "sheet.png"
            img.save(path)
            run("slice_sheet.py", path, Path(tmp) / "f", "--rows", "2", "--prefix", "atk")
            frames = sorted((Path(tmp) / "f").glob("atk_*.png"))
            self.assertEqual(len(frames), 6)
            self.assertEqual(Image.open(frames[0]).height, 200, "full row height keeps the ground line")


class FxSheetTest(unittest.TestCase):
    def test_black_becomes_alpha_without_dark_edge(self):
        with tempfile.TemporaryDirectory() as tmp:
            img = Image.new("RGB", (200, 200), (6, 6, 6))
            d = ImageDraw.Draw(img)
            for cx, cy in ((50, 50), (150, 50), (50, 150), (150, 150)):
                d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=(255, 200, 60))
            d.line((100, 0, 100, 200), fill=(200, 200, 200), width=2)  # grid line drawn by the generator
            path = Path(tmp) / "fx.png"
            img.save(path)
            run("fx_sheet.py", path, Path(tmp) / "o", "--cols", "2", "--rows", "2", "--prefix", "glow")
            f = np.array(Image.open(Path(tmp) / "o" / "glow_1.png"))
            self.assertEqual(f[0, 0, 3], 0, "background transparent")
            self.assertEqual(f[f.shape[0] // 2, f.shape[1] // 2, 3], 255, "core opaque")
            self.assertTrue((Path(tmp) / "o" / "preview.gif").exists())


class VideoCycleTest(unittest.TestCase):
    def test_finds_the_loop_period(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "frames"
            src.mkdir()
            for i in range(80):
                img = Image.new("RGB", (64, 64), FLOW_GREEN)
                x = 4 + (i % 20) * 2  # ramp: each phase of the 20-frame cycle has its own position
                ImageDraw.Draw(img).rectangle((x, 20, x + 10, 50), fill=(20, 20, 20))
                img.save(src / f"f_{i:03d}.png")
            out = json.loads(run("video_cycle.py", src, Path(tmp) / "c", "--frames", "4", "--period-min", "14"))
            self.assertEqual(out["period"] % 20, 0)
            self.assertEqual(len(list((Path(tmp) / "c").glob("walk_*.png"))), 4)


class ImportAndBoardTest(unittest.TestCase):
    def test_provenance_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            dl = Path(tmp) / "Some_flow_name_2026.jpg"
            Image.new("RGB", (8, 8), FLOW_GREEN).save(dl)
            prompt = Path(tmp) / "p.txt"
            prompt.write_text("A sheet of icons\n", encoding="utf-8")
            usage = Path(tmp) / "u.json"
            usage.write_text('{"frames": [1, 2], "fps": 10}', encoding="utf-8")
            dest = Path(tmp) / "art" / "icons.jpg"
            run("flow_import.py", dl, dest, "--url", "https://flow.google.com/project/x/edit/y", "--prompt-file",
                prompt, "--refs", "masters/hero.jpg", "--usage", usage, "--note", "2nd of 3 attempts")
            meta = json.loads(Path(f"{dest}.json").read_text(encoding="utf-8"))
            self.assertEqual(meta["prompt"], "A sheet of icons")
            self.assertEqual(meta["refs"], ["masters/hero.jpg"])
            self.assertEqual(meta["usage"]["fps"], 10)
            self.assertEqual(len(meta["sha256"]), 64)
            with self.assertRaises(AssertionError):
                run("flow_import.py", dl, dest, "--url", "u", "--prompt-file", prompt)

    def test_board_and_preview_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i in range(3):
                sheet(FLOW_GREEN, [((20 + i * 5, 10, 60 + i * 5, 90), (30, 30, 40))], (100, 100)).save(
                    Path(tmp) / f"w_{i}.png")
            run("review_board.py", Path(tmp) / "board.png", "--row", f"NEW:{tmp}/w_*.png", "--height", "80",
                "--also", "40")
            self.assertGreater(Image.open(Path(tmp) / "board.png").width, 3 * 80 * 0.5)
            run("preview_anim.py", *sorted(Path(tmp).glob("w_*.png")), "--out", Path(tmp) / "p.gif")
            self.assertEqual(Image.open(Path(tmp) / "p.gif").n_frames, 3)
            run("pad_16x9.py", Path(tmp) / "w_0.png", Path(tmp) / "wide.png", "--height", "180")
            self.assertEqual(Image.open(Path(tmp) / "wide.png").size, (320, 180))


if __name__ == "__main__":
    unittest.main()
