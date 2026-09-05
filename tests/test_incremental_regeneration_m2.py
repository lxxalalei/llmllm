import pytest

from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.l1_generator import EngineeringFactBatch, EngineeringFactDraft, L1Generator
from app.knowledge.l2_generator import (
    EngineeringRuleBatch,
    EngineeringRuleDraft,
    L2Generator,
)
from app.knowledge.models import KnowledgeItem, SourceBinding
from app.knowledge.regeneration import regenerate_go_file


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


def _l2() -> KnowledgeItem:
    return KnowledgeItem(
        id="eng.demo.channel.create.standard_flow",
        title="Standard flow",
        layer=KnowledgeLayer.L2_ENGINEERING_RULE,
        module="demo.channel",
        feature="creation",
        content="# Standard flow\n\nChange returns 1 and Keep returns 2.",
        status=KnowledgeStatus.DRAFT,
        version=1,
        derived_from=[
            "eng.demo.channel.create.changed_rule",
            "eng.demo.channel.create.kept_rule",
        ],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST, UserRole.PRODUCT],
    )


def _l3() -> KnowledgeItem:
    return KnowledgeItem(
        id="product.demo.channel.create.behavior",
        title="Creation behavior",
        layer=KnowledgeLayer.L3_PRODUCT_LOGIC,
        module="demo.channel",
        feature="creation",
        content="Product behavior.",
        status=KnowledgeStatus.PUBLISHED,
        version=1,
        derived_from=["eng.demo.channel.create.standard_flow"],
        visible_roles=[UserRole.USER, UserRole.PRODUCT, UserRole.TEST, UserRole.DEVELOPER],
    )


class ChangedFactExtractor:
    async def extract(self, symbols):
        raise AssertionError("incremental path expected")

    async def extract_incremental(self, symbols, existing_facts):
        assert [symbol.name for symbol in symbols] == ["Change"]
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="changed_rule",
                    symbol="Change",
                    title="Change value",
                    statement="Change returns 3.",
                )
            ]
        )


class ChangedRuleExtractor:
    def __init__(self) -> None:
        self.fact_ids: list[str] = []
        self.existing_ids: list[str] = []

    async def extract(self, facts, existing_rules):
        self.fact_ids = [item.id for item in facts]
        self.existing_ids = [item.id for item in existing_rules]
        return EngineeringRuleBatch(
            rules=[
                EngineeringRuleDraft(
                    key="standard_flow",
                    title="Standard flow",
                    statement="Change returns 3 and Keep returns 2.",
                    derived_from=[
                        "eng.demo.channel.create.changed_rule",
                        "eng.demo.channel.create.kept_rule",
                    ],
                )
            ]
        )


@pytest.mark.asyncio
async def test_m2_regenerates_l2_from_current_l1_and_routes_l3_to_review() -> None:
    changed = _l1(
        "eng.demo.channel.create.changed_rule",
        "Change",
        "Change value",
        "Change returns 1.",
    )
    kept = _l1(
        "eng.demo.channel.create.kept_rule",
        "Keep",
        "Keep value",
        "Keep returns 2.",
    )
    catalog = KnowledgeCatalog([changed, kept, _l2(), _l3()])
    rule_extractor = ChangedRuleExtractor()

    report = await regenerate_go_file(
        catalog=catalog,
        repo="demo/repo",
        baseline="c1",
        after="c2",
        old_file="channel.go",
        new_file="channel.go",
        old_source=OLD_GO,
        new_source=NEW_GO,
        l1_generator=L1Generator(ChangedFactExtractor()),
        l2_generator=L2Generator(rule_extractor),
    )

    assert set(rule_extractor.fact_ids) == {
        "eng.demo.channel.create.changed_rule",
        "eng.demo.channel.create.kept_rule",
    }
    assert rule_extractor.existing_ids == ["eng.demo.channel.create.standard_flow"]

    l2_changes = {item["id"]: item["change"] for item in report["l2_changes"]}
    assert l2_changes["eng.demo.channel.create.standard_flow"] == "changed"
    l2_items = {item["id"]: item for item in report["l2_items"]}
    assert l2_items["eng.demo.channel.create.standard_flow"]["version"] == 2
    assert report["l3_review"] == ["product.demo.channel.create.behavior"]


class SameFactExtractor:
    async def extract(self, symbols):
        raise AssertionError("incremental path expected")

    async def extract_incremental(self, symbols, existing_facts):
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="changed_rule",
                    symbol="Change",
                    title="Change value",
                    statement="Change returns 1.",
                )
            ]
        )


class MustNotRunL2:
    async def extract(self, facts, existing_rules):
        raise AssertionError("L2 should not run when L1 semantics are unchanged")


@pytest.mark.asyncio
async def test_m2_skips_l2_and_l3_review_when_l1_semantics_are_unchanged() -> None:
    changed = _l1(
        "eng.demo.channel.create.changed_rule",
        "Change",
        "Change value",
        "Change returns 1.",
    )
    kept = _l1(
        "eng.demo.channel.create.kept_rule",
        "Keep",
        "Keep value",
        "Keep returns 2.",
    )
    catalog = KnowledgeCatalog([changed, kept, _l2(), _l3()])

    report = await regenerate_go_file(
        catalog=catalog,
        repo="demo/repo",
        baseline="c1",
        after="c2",
        old_file="channel.go",
        new_file="channel.go",
        old_source=OLD_GO,
        new_source=NEW_GO,
        l1_generator=L1Generator(SameFactExtractor()),
        l2_generator=L2Generator(MustNotRunL2()),
    )

    assert all(item["change"] == "unchanged" for item in report["l1_changes"])
    assert all(item["change"] == "unchanged" for item in report["l2_changes"])
    assert report["l3_review"] == []
