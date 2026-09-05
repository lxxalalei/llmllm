import pytest

from app.integrations.github import GitHubChangedFile
from scripts import regenerate_mattermost_change as script


class FakeGitHubClient:
    def __init__(self, *args, **kwargs) -> None:
        self.closed = False

    async def compare_files(self, repository: str, before: str, after: str):
        return [GitHubChangedFile(path="server/public/model/user.go", status="modified")]

    async def close(self) -> None:
        self.closed = True


def test_target_change_matches_rename_from_tracked_file() -> None:
    changed = [
        GitHubChangedFile(
            path="server/channels/app/channel_create.go",
            previous_path=script.SOURCE_FILE,
            status="renamed",
        )
    ]
    target = script._target_change(changed)
    assert target is not None
    assert target.previous_path == script.SOURCE_FILE


@pytest.mark.asyncio
async def test_no_tracked_file_change_does_not_require_llm(monkeypatch) -> None:
    monkeypatch.setattr(script.KnowledgeCatalog, "from_directory", lambda root: object())
    monkeypatch.setattr(
        script,
        "bound_source_baselines",
        lambda catalog, repository, ref: {script.SOURCE_FILE: "1" * 40},
    )
    monkeypatch.setattr(script, "GitHubSourceClient", FakeGitHubClient)

    def must_not_configure_generators():
        raise AssertionError("LLM generators should not be created when tracked source is unchanged")

    monkeypatch.setattr(script, "_configured_generators", must_not_configure_generators)

    report = await script._run("2" * 40)
    assert report["changed"] is False
    assert report["reason"] == "tracked source file is unchanged in compare range"
    assert report["baseline"] == "1" * 40
    assert report["after"] == "2" * 40
