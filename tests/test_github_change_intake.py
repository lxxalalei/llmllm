import pytest

from app.integrations.github import GitHubChangedFile, analyze_repository_change
from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.models import KnowledgeItem, SourceBinding

OLD_GO = """package p

func CreateChannel() int {
    return 1
}
"""

NEW_GO = """package p

func CreateChannel() int {
    return 2
}
"""


class FakeGitHubClient:
    async def compare_files(self, repository: str, before: str, after: str):
        return [
            GitHubChangedFile(path="f.go", status="modified"),
            GitHubChangedFile(path="untracked.go", status="modified"),
        ]

    async def fetch_text(self, repository: str, ref: str, path: str):
        if path == "untracked.go":
            return "package p\nfunc Other() {}\n"
        return OLD_GO if ref == "c1" else NEW_GO


def _catalog() -> KnowledgeCatalog:
    l1 = KnowledgeItem(
        id="l1.create",
        title="create",
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="m",
        content="fact",
        status=KnowledgeStatus.DRAFT,
        sources=[
            SourceBinding(
                repo="r",
                commit="c1",
                file="f.go",
                symbol="CreateChannel",
            )
        ],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )
    l2 = KnowledgeItem(
        id="l2.create",
        title="rule",
        layer=KnowledgeLayer.L2_ENGINEERING_RULE,
        module="m",
        content="rule",
        status=KnowledgeStatus.DRAFT,
        derived_from=["l1.create"],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )
    return KnowledgeCatalog([l1, l2])


@pytest.mark.asyncio
async def test_repository_change_only_analyzes_tracked_source_files() -> None:
    report = await analyze_repository_change(
        _catalog(),
        repository="r",
        before="c1",
        after="c2",
        client=FakeGitHubClient(),
    )
    assert report["tracked_files"] == ["f.go"]
    assert [item["path"] for item in report["files"]] == ["f.go"]
    assert report["bound_l1"] == ["l1.create"]
    assert report["affected"] == ["l1.create", "l2.create"]
    assert {item["id"] for item in report["transitions"]} == {
        "l1.create",
        "l2.create",
    }


@pytest.mark.asyncio
async def test_repository_change_without_bound_commit_skips_remote_compare() -> None:
    class MustNotCall:
        async def compare_files(self, *args, **kwargs):
            raise AssertionError("compare should not run")

    report = await analyze_repository_change(
        _catalog(),
        repository="r",
        before="unknown",
        after="c2",
        client=MustNotCall(),
    )
    assert report["tracked_files"] == []
    assert report["files"] == []
