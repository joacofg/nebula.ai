"""Find and rewrite the generated blocks of the thesis source.

A block is ``<!-- GEN:name -->`` + newline + content + newline + ``<!-- /GEN:name -->``.
Names are unique across every Markdown file of the thesis directory.
"""

from __future__ import annotations

import re
from pathlib import Path

OPEN = re.compile(r"<!-- GEN:([a-z0-9-]+) -->")


class BlockError(ValueError):
    pass


def _pattern(name: str) -> re.Pattern[str]:
    n = re.escape(name)
    return re.compile(rf"(<!-- GEN:{n} -->\n)(.*?)(\n<!-- /GEN:{n} -->)", re.DOTALL)


def find_blocks(root: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    for path in sorted(root.glob("*.md")):
        for name in OPEN.findall(path.read_text(encoding="utf-8")):
            if name in found:
                raise BlockError(f"GEN block {name!r} appears in {found[name]} and {path}")
            found[name] = path
    return found


def replace_block(text: str, name: str, content: str) -> str:
    pattern = _pattern(name)
    if not pattern.search(text):
        raise BlockError(f"No GEN block {name!r} in the thesis source.")
    return pattern.sub(lambda m: m.group(1) + content + m.group(3), text, count=1)


def _current(text: str, name: str) -> str:
    match = _pattern(name).search(text)
    if not match:
        raise BlockError(f"GEN block {name!r} is not closed.")
    return match.group(2)


def apply(contents: dict[str, str], root: Path, *, write: bool) -> list[str]:
    """Rewrite every block; return the names whose content changed. ``write=False`` is a dry run."""
    located = find_blocks(root)
    missing, unknown = sorted(set(located) - set(contents)), sorted(set(contents) - set(located))
    if missing or unknown:
        raise BlockError(f"no generator for {missing}; no block in the thesis for {unknown}")
    stale: list[str] = []
    texts = {path: path.read_text(encoding="utf-8") for path in set(located.values())}
    for name in sorted(contents):
        path = located[name]
        if _current(texts[path], name) != contents[name]:
            stale.append(name)
            texts[path] = replace_block(texts[path], name, contents[name])
    if write:
        for path in {located[n] for n in stale}:
            path.write_text(texts[path], encoding="utf-8")
    return stale


def update_block(name: str, content: str, root: Path) -> None:
    located = find_blocks(root)
    if name not in located:
        raise BlockError(f"No GEN block {name!r} in {root}.")
    path = located[name]
    path.write_text(replace_block(path.read_text(encoding="utf-8"), name, content), encoding="utf-8")
