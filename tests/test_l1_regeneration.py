import pytest

from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.l1_generator import EngineeringFactBatch, EngineeringFactDraft, L1Generator
from app.knowledge.models import KnowledgeItem, SourceBinding
from app.knowledge.regeneration import regenerate_go_file_l1


OLD_GO = """package p

func Change() int {
    return 1
}

func Keep() int {
    return 2
}
"""

NEW_GO = """package p

func Change() int {
    return 3
}

// line drift only
func Keep() int {
    return 2
}
"""


def _l1(item_id: str, symbol: str, title: str, statement: str) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=title,
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="demo.channel",
        feature="creation",
        content=f"# {title}\n\n{statement}",
        status=KnowledgeStatus.DRAFT,
        version=1,
        sources=[
            SourceBinding(
                repo="demo/repo",
                ref="main",
                commit="c1",
                file="channel.go",
                symbol=symbol,
            )
        ],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )


class IncrementalExtractor:
    def __init__(self) -> None:
        self.symbols: list[str] = []
        self.existing_ids: list[str] = []

    async def extract(self, symbols):
        raise AssertionError("full extraction should not be used for a modified bound symbol")

    async def extract_incremental(self, symbols, existing_facts):
        self.symbols = [symbol.name for symbol in symbols]
        self.existing_ids = [item.id for item in existing_facts]
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="changed_rule",
                    symbol="Change",
                    title="Change returns the configured value",
                    statement="Change now returns 3.",
                )
            ]
        )


@pytest.mark.asyncio
async def test_incremental_l1_regenerates_only_changed_symbol_and_advances_file_baseline() -> None:
    changed = _l1(
        "eng.demo.channel.create.changed_rule",
        "Change",
        "Change returns the configured value",
        "Change returns 1.",
    )
    kept = _l1(
        "eng.demo.channel.create.kept_rule",
        "Keep",
        "Keep returns a constant",
        "Keep returns 2.",
    )
    catalog = KnowledgeCatalog([changed, kept])
    extractor = IncrementalExtractor()
    generator = L1Generator(extractor)

    report = await regenerate_go_file_l1(
        catalog=catalog,
        repo="demo/repo",
        baseline="c1",
        after="c2",
        old_file="channel.go",
        new_file="channel.go",
        old_source=OLD_GO,
        new_source=NEW_GO,
        l1_generator=generator,
    )

    assert extractor.symbols == ["Change"]
    assert extractor.existing_ids == ["eng.demo.channel.create.changed_rule"]
    changes = {item["id"]: item["change"] for item in report["l1_changes"]}
    assert changes["eng.demo.channel.create.changed_rule"] == "changed"
    assert changes["eng.demo.channel.create.kept_rule"] == "unchanged"

    items = {item["id"]: item for item in report["l1_items"]}
    assert items["eng.demo.channel.create.changed_rule"]["version"] == 2
    assert items["eng.demo.channel.create.changed_rule"]["sources"][0]["commit"] == "c2"
    assert items["eng.demo.channel.create.kept_rule"]["sources"][0]["commit"] == "c2"
    assert items["eng.demo.channel.create.kept_rule"]["sources"][0]["start_line"] > 0


class MustNotExtract:
    async def extract(self, symbols):
        raise AssertionError("removed symbols have no new source to extract")

    async def extract_incremental(self, symbols, existing_facts):
        raise AssertionError("removed symbols have no new source to extract")


@pytest.mark.asyncio
async def test_removed_symbol_removes_bound_l1_without_model_call() -> None:
    removed = _l1(
        "eng.demo.channel.create.removed_rule",
        "Change",
        "Removed fact",
        "Change returns 1.",
    )
    kept = _l1(
        "eng.demo.channel.create.kept_rule",
        "Keep",
        "Keep returns a constant",
        "Keep returns 2.",
    )
    catalog = KnowledgeCatalog([removed, kept])
    generator = L1Generator(MustNotExtract())
    new_source = """package p

func Keep() int {
    return 2
}
"""

    report = await regenerate_go_file_l1(
        catalog=catalog,
        repo="demo/repo",
        baseline="c1",
        after="c2",
        old_file="channel.go",
        new_file="channel.go",
        old_source=OLD_GO,
        new_source=new_source,
        l1_generator=generator,
    )

    changes = {item["id"]: item["change"] for item in report["l1_changes"]}
    assert changes["eng.demo.channel.create.removed_rule"] == "removed"
    assert changes["eng.demo.channel.create.kept_rule"] == "unchanged"
    assert {item["id"] for item in report["l1_items"]} == {
        "eng.demo.channel.create.kept_rule"
    }
