from pathlib import Path

from app.code_index.inventory import inventory_repository


def test_repository_inventory_lists_supported_files_and_symbols(tmp_path: Path) -> None:
    (tmp_path / "service").mkdir()
    (tmp_path / "service" / "channel.go").write_text(
        "package service\n\nfunc CreateChannel() {}\nfunc ArchiveChannel() {}\n",
        encoding="utf-8",
    )
    (tmp_path / "tools.py").write_text(
        "def rebuild():\n    return True\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("ignored", encoding="utf-8")

    report = inventory_repository(tmp_path).to_dict()

    assert report["summary"] == {
        "files": 2,
        "symbols": 3,
        "languages": {"go": 1, "python": 1},
    }
    files = {item["path"]: item for item in report["files"]}
    assert [symbol["name"] for symbol in files["service/channel.go"]["symbols"]] == [
        "CreateChannel",
        "ArchiveChannel",
    ]
    assert [symbol["name"] for symbol in files["tools.py"]["symbols"]] == ["rebuild"]


def test_repository_inventory_respects_requested_scope(tmp_path: Path) -> None:
    (tmp_path / "channel").mkdir()
    (tmp_path / "team").mkdir()
    (tmp_path / "channel" / "a.go").write_text(
        "package channel\nfunc A() {}\n", encoding="utf-8"
    )
    (tmp_path / "team" / "b.go").write_text(
        "package team\nfunc B() {}\n", encoding="utf-8"
    )

    report = inventory_repository(tmp_path, paths=["channel"]).to_dict()

    assert [item["path"] for item in report["files"]] == ["channel/a.go"]
