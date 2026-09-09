import pytest

from scripts.compile_l4 import validate_output_path


def test_preview_output_cannot_write_into_canonical_knowledge(tmp_path):
    root = tmp_path / "knowledge"
    root.mkdir()
    with pytest.raises(ValueError, match="canonical"):
        validate_output_path(root / "preview.json", [root], [])


def test_preview_output_cannot_replace_its_input_or_use_markdown(tmp_path):
    source = tmp_path / "manifest.json"
    with pytest.raises(ValueError, match="input"):
        validate_output_path(source, [], [source])
    with pytest.raises(ValueError, match="JSON"):
        validate_output_path(tmp_path / "preview.md", [], [])
    validate_output_path(tmp_path / "preview.json", [], [source])
