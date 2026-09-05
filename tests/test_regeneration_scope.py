import pytest

from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.l1_generator import EngineeringFactBatch, EngineeringFactDraft, L1Generator
from app.knowledge.models import KnowledgeItem, SourceBinding
from app.knowledge.regeneration import regenerate_go_file_l1


def _l1() -> KnowledgeItem:
    return KnowledgeItem(
        id="eng.demo.channel.create.bound_fact",
        title="Bound fact",
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="demo.channel",
        feature="creation",
        content="Bound returns 1.",
        status=KnowledgeStatus.DRAFT,
        sources=[
            SourceBinding(
                repo="demo/repo",
                ref="main",
                commit="c1",
                file="channel.go",
                symbol="Bound",
            )
        ],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )


class ScopeExtractor:
    def __init__(self) -> None:
        self.symbols: list[str] = []

    async def extract(self, symbols):
        raise AssertionError("incremental path expected")

    async def extract_incremental(self, symbols, existing_facts):
        self.symbols = [symbol.name for symbol in symbols]
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="bound_fact",
                    symbol="Bound",
                    title="Bound fact",
                    statement="Bound returns 2.",
                )
            ]
        )


@pytest.mark.asyncio
async def test_unbound_changed_symbol_is_reported_but_not_absorbed_into_feature() -> None:
    old_source = """package p

func Bound() int {
    return 1
}

func Unbound() int {
    return 10
}
"""
    new_source = """package p

func Bound() int {
    return 2
}

func Unbound() int {
    return 20
}
"""
    extractor = ScopeExtractor()
    report = await regenerate_go_file_l1(
        catalog=KnowledgeCatalog([_l1()]),
        repo="demo/repo",
        baseline="c1",
        after="c2",
        old_file="channel.go",
        new_file="channel.go",
        old_source=old_source,
        new_source=new_source,
        l1_generator=L1Generator(extractor),
    )

    assert extractor.symbols == ["Bound"]
    assert report["unbound_symbol_changes"] == [
        {"name": "Unbound", "change": "modified"}
    ]
    assert {item["id"] for item in report["l1_items"]} == {
        "eng.demo.channel.create.bound_fact"
    }
