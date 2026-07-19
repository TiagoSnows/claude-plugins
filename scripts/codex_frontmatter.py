"""Strict, dependency-free projection of Claude skill frontmatter to Codex."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

ALLOWED_FRONTMATTER = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
}
TOP_LEVEL_KEY = re.compile(r"^([A-Za-z0-9_-]+):(?:[ \t].*)?$")
CODEX_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class GenerationError(RuntimeError):
    """Raised when the canonical source cannot be transformed safely."""


def split_frontmatter(text: str, source: PurePosixPath) -> tuple[list[str], str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.startswith("---\n"):
        raise GenerationError(f"{source}: SKILL.md must start with YAML frontmatter")
    closing = re.search(r"(?m)^---$", normalized[4:])
    if closing is None:
        raise GenerationError(f"{source}: YAML frontmatter is not closed")
    closing_start = 4 + closing.start()
    closing_end = 4 + closing.end()
    frontmatter = normalized[4:closing_start].removesuffix("\n")
    return frontmatter.split("\n"), normalized[closing_end:]


def frontmatter_blocks(
    lines: list[str], source: PurePosixPath
) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    seen: set[str] = set()
    current: tuple[str, list[str]] | None = None
    for line in lines:
        match = TOP_LEVEL_KEY.match(line)
        if match:
            key = match.group(1)
            if key in seen:
                raise GenerationError(f"{source}: duplicate frontmatter key: {key}")
            seen.add(key)
            current = (key, [line])
            blocks.append(current)
        elif current is None:
            if line.strip() and not line.lstrip().startswith("#"):
                raise GenerationError(
                    f"{source}: content appears before the first frontmatter key"
                )
        else:
            current[1].append(line)
    return blocks


def valid_codex_name(name: str) -> bool:
    return bool(CODEX_NAME.fullmatch(name)) and len(name) <= 64


def metadata_direct_layout(
    lines: list[str], source: PurePosixPath
) -> tuple[set[str], str]:
    candidates: list[tuple[str, str]] = []
    for line in lines[1:]:
        stripped = line.lstrip(" \t")
        if not stripped or stripped.startswith("#"):
            continue
        candidates.append((line[: len(line) - len(stripped)], stripped))
    if not candidates:
        return set(), "  "
    direct_width = min(len(indent) for indent, _ in candidates)
    direct_lines = [item for item in candidates if len(item[0]) == direct_width]
    direct_indent = direct_lines[0][0]
    if not direct_indent or "\t" in direct_indent:
        raise GenerationError(f"{source}: metadata indentation must use spaces")
    keys: set[str] = set()
    key_pattern = re.compile(r"^(?:([A-Za-z0-9_-]+)|'([^']+)'|\"([^\"]+)\")\s*:")
    for indent, stripped in direct_lines:
        if indent != direct_indent:
            raise GenerationError(f"{source}: metadata indentation is inconsistent")
        match = key_pattern.match(stripped)
        if match is None:
            raise GenerationError(f"{source}: metadata must be a YAML mapping")
        keys.add(next(group for group in match.groups() if group is not None))
    return keys, direct_indent


def merge_claude_metadata(
    allowed: list[tuple[str, list[str]]],
    claude_only: list[list[str]],
    source: PurePosixPath,
) -> None:
    metadata = next((block for key, block in allowed if key == "metadata"), None)
    if metadata is None:
        metadata = ["metadata:"]
        allowed.append(("metadata", metadata))
    elif metadata[0].strip() != "metadata:":
        raise GenerationError(
            f"{source}: inline metadata cannot safely receive Claude-only fields"
        )
    metadata_keys, child_indent = metadata_direct_layout(metadata, source)
    if "claude" in metadata_keys:
        raise GenerationError(f"{source}: metadata.claude is already defined")
    metadata.append(f"{child_indent}claude:")
    nested_indent = child_indent + "  "
    for block in claude_only:
        metadata.extend(f"{nested_indent}{line}" if line else line for line in block)


def sanitize_skill(contents: bytes, source: PurePosixPath, skill_name: str) -> bytes:
    try:
        text = contents.decode("utf-8")
    except UnicodeDecodeError as error:
        raise GenerationError(f"{source}: SKILL.md is not valid UTF-8") from error

    lines, body = split_frontmatter(text, source)
    blocks = frontmatter_blocks(lines, source)
    allowed: list[tuple[str, list[str]]] = []
    claude_only: list[list[str]] = []
    found_keys = {key for key, _ in blocks}
    for key, block in blocks:
        if key == "name":
            raw_name = block[0].partition(":")[2].strip().strip("'\"")
            if not valid_codex_name(raw_name) or raw_name != skill_name:
                claude_only.append(block)
                allowed.append(("name", [f"name: {skill_name}"]))
            else:
                allowed.append((key, block))
        elif key in ALLOWED_FRONTMATTER:
            allowed.append((key, block))
        else:
            claude_only.append(block)
    if not {"name", "description"}.issubset(found_keys):
        raise GenerationError(f"{source}: frontmatter requires name and description")
    if not valid_codex_name(skill_name):
        raise GenerationError(f"{source}: directory name is not Codex-compatible")
    if claude_only:
        merge_claude_metadata(allowed, claude_only, source)

    rendered = ["---"]
    for _, block in allowed:
        rendered.extend(block)
    return ("\n".join(rendered) + "\n---" + body).encode("utf-8")
