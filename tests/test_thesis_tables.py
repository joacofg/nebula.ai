from pathlib import Path

import pytest

from scripts.thesis import blocks


def _write(root: Path, name: str, body: str) -> Path:
    path = root / name
    path.write_text(body, encoding="utf-8")
    return path


def test_find_blocks_across_files(tmp_path):
    _write(tmp_path, "a.md", "x\n<!-- GEN:one -->\nold\n<!-- /GEN:one -->\n")
    _write(tmp_path, "b.md", "<!-- GEN:two -->\n\n<!-- /GEN:two -->\n")
    assert blocks.find_blocks(tmp_path) == {"one": tmp_path / "a.md", "two": tmp_path / "b.md"}


def test_duplicate_block_name_is_an_error(tmp_path):
    _write(tmp_path, "a.md", "<!-- GEN:one -->\nx\n<!-- /GEN:one -->\n")
    _write(tmp_path, "b.md", "<!-- GEN:one -->\ny\n<!-- /GEN:one -->\n")
    with pytest.raises(blocks.BlockError, match="one"):
        blocks.find_blocks(tmp_path)


def test_replace_is_literal():
    text = "<!-- GEN:one -->\nold\n<!-- /GEN:one -->"
    out = blocks.replace_block(text, "one", r"ruta C:\1 y \g<0>")
    assert out == "<!-- GEN:one -->\nruta C:\\1 y \\g<0>\n<!-- /GEN:one -->"


def test_missing_block_is_an_error():
    with pytest.raises(blocks.BlockError, match="nope"):
        blocks.replace_block("sin bloques", "nope", "x")


def test_apply_reports_stale_and_check_does_not_write(tmp_path):
    path = _write(tmp_path, "a.md", "<!-- GEN:one -->\nold\n<!-- /GEN:one -->\n")
    assert blocks.apply({"one": "new"}, tmp_path, write=False) == ["one"]
    assert "old" in path.read_text(encoding="utf-8")
    assert blocks.apply({"one": "new"}, tmp_path, write=True) == ["one"]
    assert blocks.apply({"one": "new"}, tmp_path, write=False) == []


def test_apply_rejects_unknown_and_missing_names(tmp_path):
    _write(tmp_path, "a.md", "<!-- GEN:one -->\nold\n<!-- /GEN:one -->\n")
    with pytest.raises(blocks.BlockError, match="two"):
        blocks.apply({"one": "x", "two": "y"}, tmp_path, write=False)
    with pytest.raises(blocks.BlockError, match="one"):
        blocks.apply({}, tmp_path, write=False)


def test_update_block_finds_the_file(tmp_path):
    path = _write(tmp_path, "b.md", "a\n<!-- GEN:two -->\nold\n<!-- /GEN:two -->\nz\n")
    blocks.update_block("two", "new", tmp_path)
    assert path.read_text(encoding="utf-8") == "a\n<!-- GEN:two -->\nnew\n<!-- /GEN:two -->\nz\n"
