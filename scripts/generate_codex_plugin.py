#!/usr/bin/env python3
"""Generate the Codex PBES skill tree from the canonical Claude distribution."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Iterator

from codex_frontmatter import GenerationError, sanitize_skill

MANIFEST_NAME = ".generated-files.json"
SENSITIVE_NAMES = {
    ".netrc",
    ".npmrc",
    ".pypirc",
    "connections.json",
    "credentials.json",
    "secrets.json",
}
SENSITIVE_SUFFIXES = {".key", ".kdbx", ".p12", ".pem", ".pfx", ".pyc"}
LOCAL_CONFIG_SUFFIXES = {
    ".local.json",
    ".local.toml",
    ".local.yaml",
    ".local.yml",
}
IGNORED_DIRECTORIES = {
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "node_modules",
    "venv",
}
SECRET_PATTERNS = (
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"AKIA[0-9A-Z]{16}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"xox[baprs]-[A-Za-z0-9-]{20,}"),
)
EXPECTED_SKILL_COUNT = 90


def is_safe_source(path: PurePosixPath) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return (
        not {".", ".."}.intersection(path.parts)
        and not lowered_parts.intersection(IGNORED_DIRECTORIES)
        and name not in SENSITIVE_NAMES
        and not name.startswith(".env")
        and not any(name.endswith(suffix) for suffix in LOCAL_CONFIG_SUFFIXES)
        and path.suffix.lower() not in SENSITIVE_SUFFIXES
    )


def contains_secret_pattern(contents: bytes) -> bool:
    if b"\0" in contents[:8192]:
        return False
    return any(pattern.search(contents) for pattern in SECRET_PATTERNS)


def parse_tracked_sources(output: bytes) -> list[PurePosixPath]:
    paths: list[PurePosixPath] = []
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0]
        path = PurePosixPath(raw_path.decode("utf-8"))
        if mode not in {b"100644", b"100755"}:
            raise GenerationError(f"unsupported tracked file mode {mode.decode()}: {path}")
        paths.append(path)
    return paths


def tracked_sources(repo_root: Path) -> list[PurePosixPath]:
    result = subprocess.run(
        ["git", "ls-files", "-s", "-z", "--", "pbes/skills", "pbes/NOTICE.md"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    paths = parse_tracked_sources(result.stdout)
    safe_paths = sorted(path for path in paths if is_safe_source(path))
    notice = PurePosixPath("pbes/NOTICE.md")
    if notice not in safe_paths:
        raise GenerationError("canonical distribution is missing pbes/NOTICE.md")
    descriptors = [path for path in safe_paths if path.name == "SKILL.md"]
    if len(descriptors) != EXPECTED_SKILL_COUNT:
        raise GenerationError(
            f"expected {EXPECTED_SKILL_COUNT} tracked skills, found {len(descriptors)}"
        )
    return safe_paths


def expected_files(repo_root: Path) -> dict[PurePosixPath, bytes]:
    expected: dict[PurePosixPath, bytes] = {}
    canonical_root = (repo_root / "pbes").resolve()
    for source in tracked_sources(repo_root):
        source_path = repo_root / source.as_posix()
        resolved_source = source_path.resolve(strict=True)
        if source_path.is_symlink() or not resolved_source.is_relative_to(canonical_root):
            raise GenerationError(f"refusing source outside canonical tree: {source}")
        if source == PurePosixPath("pbes/NOTICE.md"):
            destination = PurePosixPath("NOTICE.md")
        else:
            relative = source.relative_to("pbes/skills")
            destination = PurePosixPath("skills") / relative
        contents = source_path.read_bytes()
        if contains_secret_pattern(contents):
            raise GenerationError(f"possible secret detected in source: {source}")
        if source.name == "SKILL.md":
            contents = sanitize_skill(contents, source, source.parent.name)
        expected[destination] = contents
    return expected


def manifest_bytes(paths: set[PurePosixPath]) -> bytes:
    payload = {
        "schemaVersion": 1,
        "source": "pbes/skills",
        "files": [path.as_posix() for path in sorted(paths)],
    }
    return (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def actual_managed_files(plugin_root: Path) -> set[PurePosixPath]:
    files: set[PurePosixPath] = set()
    skills_root = plugin_root / "skills"
    if plugin_root.is_symlink() or skills_root.is_symlink():
        raise GenerationError("generated plugin paths must not be symlinks")
    if skills_root.is_dir():
        for path in skills_root.rglob("*"):
            if path.is_symlink():
                raise GenerationError(f"generated path must not be a symlink: {path}")
            if path.is_file():
                files.add(PurePosixPath(path.relative_to(plugin_root).as_posix()))
    notice = plugin_root / "NOTICE.md"
    if notice.is_symlink():
        raise GenerationError("generated NOTICE.md must not be a symlink")
    if notice.is_file():
        files.add(PurePosixPath("NOTICE.md"))
    return files


def write_if_changed(path: Path, contents: bytes) -> bool:
    if path.is_symlink():
        raise GenerationError(f"refusing to write through symlink: {path}")
    if path.is_file() and path.read_bytes() == contents:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(contents)
        os.replace(temporary, path)
        return True
    finally:
        temporary.unlink(missing_ok=True)


def set_file_lock(handle: BinaryIO, *, acquire: bool) -> None:
    handle.seek(0)
    if os.name == "nt":
        import msvcrt

        mode = msvcrt.LK_NBLCK if acquire else msvcrt.LK_UNLCK
        msvcrt.locking(handle.fileno(), mode, 1)
    else:
        import fcntl

        mode = fcntl.LOCK_EX | fcntl.LOCK_NB if acquire else fcntl.LOCK_UN
        fcntl.flock(handle.fileno(), mode)


@contextmanager
def generation_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        try:
            set_file_lock(handle, acquire=True)
        except OSError as error:
            raise GenerationError("another Codex generation is running") from error
        try:
            yield
        finally:
            set_file_lock(handle, acquire=False)


def check_generated(plugin_root: Path, expected: dict[PurePosixPath, bytes]) -> list[str]:
    errors: list[str] = []
    expected_paths = set(expected)
    actual_paths = actual_managed_files(plugin_root)
    for path in sorted(expected_paths - actual_paths):
        errors.append(f"missing generated file: {path}")
    for path in sorted(actual_paths - expected_paths):
        errors.append(f"unexpected generated file: {path}")
    for path in sorted(expected_paths & actual_paths):
        if (plugin_root / path.as_posix()).read_bytes() != expected[path]:
            errors.append(f"generated file differs from source: {path}")
    manifest = plugin_root / MANIFEST_NAME
    expected_manifest = manifest_bytes(expected_paths)
    if not manifest.is_file() or manifest.read_bytes() != expected_manifest:
        errors.append(f"{MANIFEST_NAME} is missing or stale")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the generated Codex distribution differs from its source",
    )
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    plugin_root = repo_root / "plugins" / "pbes"

    try:
        expected = expected_files(repo_root)
        if args.check:
            errors = check_generated(plugin_root, expected)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
            print(f"Codex distribution is current: {len(expected)} files")
            return 0

        with generation_lock(repo_root / ".codex-generation.lock"):
            unexpected = actual_managed_files(plugin_root) - set(expected)
            if unexpected:
                joined = ", ".join(str(path) for path in sorted(unexpected))
                raise GenerationError(
                    "refusing to delete unowned Codex files; remove explicitly: "
                    + joined
                )
            changed = sum(
                write_if_changed(plugin_root / path.as_posix(), contents)
                for path, contents in expected.items()
            )
            changed += write_if_changed(
                plugin_root / MANIFEST_NAME, manifest_bytes(set(expected))
            )
        print(f"Generated {len(expected)} files; changed {changed}")
        return 0
    except (GenerationError, OSError, subprocess.CalledProcessError) as error:
        print(f"generation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
