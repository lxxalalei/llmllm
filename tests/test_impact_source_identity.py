from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.impact import analyze_impact, bound_l1_items
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


def _l1(item_id: str, *, repo: str, file: str) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=item_id,
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="m",
        content="fact",
        status=KnowledgeStatus.DRAFT,
        sources=[
            SourceBinding(
                repo=repo,
                commit="c1",
                file=file,
                symbol="CreateChannel",
            )
        ],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )


def test_bound_l1_can_scope_full_source_identity() -> None:
    catalog = KnowledgeCatalog(
        [
            _l1("target", repo="r", file="f.go"),
            _l1("same-symbol-other-file", repo="r", file="other.go"),
            _l1("same-symbol-other-repo", repo="other", file="f.go"),
        ]
    )
    bound = bound_l1_items(
        catalog,
        "CreateChannel",
        commit="c1",
        repo="r",
        file="f.go",
    )
    assert [item.id for item in bound] == ["target"]


def test_analyze_impact_does_not_cross_file_boundary() -> None:
    catalog = KnowledgeCatalog(
        [
            _l1("target", repo="r", file="f.go"),
            _l1("other", repo="r", file="other.go"),
        ]
    )
    report = analyze_impact(
        catalog,
        OLD_GO,
        NEW_GO,
        commit="c1",
        repo="r",
        file="f.go",
    )
    assert report["bound_l1"] == ["target"]
    assert report["affected"] == ["target"]
