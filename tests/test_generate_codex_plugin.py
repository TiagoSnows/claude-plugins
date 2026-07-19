from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

SCRIPT = Path(__file__).parents[1] / "scripts" / "generate_codex_plugin.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("generate_codex_plugin", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class SanitizeSkillTests(unittest.TestCase):
    def test_preserves_claude_fields_under_metadata_and_normalizes_name(self) -> None:
        source = b"""---
name: Human Readable Name
description: Test skill
version: 3.0.0
disable-model-invocation: true
---

# Body
"""

        result = MODULE.sanitize_skill(
            source, PurePosixPath("pbes/skills/test-skill/SKILL.md"), "test-skill"
        ).decode("utf-8")

        self.assertIn("name: test-skill", result)
        self.assertIn("metadata:\n  claude:\n    name: Human Readable Name", result)
        self.assertIn("    version: 3.0.0", result)
        self.assertIn("    disable-model-invocation: true", result)
        self.assertTrue(result.endswith("\n# Body\n"))

    def test_merges_claude_fields_into_existing_metadata_mapping(self) -> None:
        source = b"""---
name: test-skill
description: Test skill
metadata:
  version: 1
argument-hint: "[target]"
---
Body
"""

        result = MODULE.sanitize_skill(
            source, PurePosixPath("pbes/skills/test-skill/SKILL.md"), "test-skill"
        ).decode("utf-8")

        self.assertIn(
            "metadata:\n  version: 1\n  claude:\n    argument-hint: \"[target]\"",
            result,
        )

    def test_preserves_existing_metadata_indentation(self) -> None:
        source = b"""---
name: test-skill
description: Test skill
metadata:
    version: 1
argument-hint: "[target]"
---
Body
"""

        result = MODULE.sanitize_skill(
            source, PurePosixPath("pbes/skills/test-skill/SKILL.md"), "test-skill"
        ).decode("utf-8")

        self.assertIn(
            "metadata:\n    version: 1\n    claude:\n      argument-hint: \"[target]\"",
            result,
        )

    def test_rejects_inline_metadata_when_claude_fields_need_merging(self) -> None:
        source = b"""---
name: test-skill
description: Test skill
metadata: {version: 1}
argument-hint: "[target]"
---
Body
"""

        with self.assertRaises(MODULE.GenerationError):
            MODULE.sanitize_skill(
                source,
                PurePosixPath("pbes/skills/test-skill/SKILL.md"),
                "test-skill",
            )

    def test_rejects_existing_inline_claude_metadata(self) -> None:
        source = b"""---
name: test-skill
description: Test skill
metadata:
  claude: {owner: upstream}
argument-hint: "[target]"
---
Body
"""

        with self.assertRaises(MODULE.GenerationError):
            MODULE.sanitize_skill(
                source,
                PurePosixPath("pbes/skills/test-skill/SKILL.md"),
                "test-skill",
            )

    def test_preserves_empty_body_and_normalizes_crlf(self) -> None:
        source = b"---\r\nname: test-skill\r\ndescription: Test\r\n---"

        result = MODULE.sanitize_skill(
            source, PurePosixPath("pbes/skills/test-skill/SKILL.md"), "test-skill"
        )

        self.assertEqual(result, b"---\nname: test-skill\ndescription: Test\n---")

    def test_rejects_duplicate_frontmatter_keys(self) -> None:
        source = b"""---
name: test-skill
name: duplicate
description: Test skill
---
Body
"""

        with self.assertRaises(MODULE.GenerationError):
            MODULE.sanitize_skill(
                source,
                PurePosixPath("pbes/skills/test-skill/SKILL.md"),
                "test-skill",
            )

    def test_filters_sensitive_and_cache_paths(self) -> None:
        unsafe = [
            "pbes/skills/postgres/connections.json",
            "pbes/skills/postgres/.env.local",
            "pbes/skills/x/.pytest_cache/state",
            "pbes/skills/x/settings.local.json",
            "pbes/skills/x/credentials.json",
            "pbes/skills/x/.npmrc",
            "pbes/skills/x/.netrc",
            "pbes/skills/x/scripts/__pycache__/x.pyc",
            "pbes/skills/x/private.pem",
            "pbes/skills/x/node_modules/package.json",
        ]

        self.assertTrue(
            all(not MODULE.is_safe_source(PurePosixPath(path)) for path in unsafe)
        )
        self.assertTrue(
            MODULE.is_safe_source(PurePosixPath("pbes/skills/x/scripts/tool.py"))
        )

    def test_rejects_symlink_mode_from_git_index(self) -> None:
        output = b"120000 abcdef 0\tpbes/skills/x/link\0"

        with self.assertRaises(MODULE.GenerationError):
            MODULE.parse_tracked_sources(output)

    def test_detects_secret_content_patterns(self) -> None:
        self.assertTrue(
            MODULE.contains_secret_pattern(b"-----BEGIN PRIVATE KEY-----\n")
        )
        self.assertFalse(MODULE.contains_secret_pattern(b"example-token-placeholder"))

    def test_check_generated_covers_drift_and_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_root = Path(directory)
            destination = plugin_root / "skills" / "x" / "SKILL.md"
            expected = {PurePosixPath("skills/x/SKILL.md"): b"expected"}

            self.assertTrue(MODULE.write_if_changed(destination, b"expected"))
            self.assertFalse(MODULE.write_if_changed(destination, b"expected"))
            MODULE.write_if_changed(
                plugin_root / MODULE.MANIFEST_NAME,
                MODULE.manifest_bytes(set(expected)),
            )
            self.assertEqual(MODULE.check_generated(plugin_root, expected), [])

            destination.write_bytes(b"drift")
            errors = MODULE.check_generated(plugin_root, expected)
            self.assertTrue(any("differs" in error for error in errors))

    def test_generation_lock_rejects_concurrent_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            lock_path = Path(directory) / ".generation.lock"

            with MODULE.generation_lock(lock_path):
                with self.assertRaises(MODULE.GenerationError):
                    with MODULE.generation_lock(lock_path):
                        self.fail("a second writer acquired the generation lock")

            self.assertTrue(lock_path.is_file())

    def test_rejects_symlink_in_generated_tree(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_root = Path(directory) / "plugin"
            skills_root = plugin_root / "skills"
            skills_root.mkdir(parents=True)
            target = Path(directory) / "outside.md"
            target.write_bytes(b"outside")
            link = skills_root / "linked.md"
            try:
                link.symlink_to(target)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")

            with self.assertRaises(MODULE.GenerationError):
                MODULE.actual_managed_files(plugin_root)


if __name__ == "__main__":
    unittest.main()
