import pytest

from app.knowledge import KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.l2_generator import (
    EngineeringRuleBatch,
    EngineeringRuleDraft,
    L2Generator,
)
from app.knowledge.models import KnowledgeItem


def _l1(item_id: str) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=item_id,
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="demo.channel",
        feature="creation",
        content="fact",
        status=KnowledgeStatus.DRAFT,
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )


class FakeRuleExtractor:
    async def extract(self, facts, existing_rules):
        return EngineeringRuleBatch(
            rules=[
                EngineeringRuleDraft(
                    key="standard_flow",
                    title="Standard flow",
                    statement="Creation follows the current engineering constraints.",
                    derived_from=[facts[0].id],
                )
            ]
        )


@pytest.mark.asyncio
async def test_l2_generator_builds_rule_from_known_l1_ids() -> None:
    generator = L2Generator(FakeRuleExtractor())
    items = await generator.generate(
        namespace="demo.channel.create",
        module="demo.channel",
        feature="creation",
        l1_items=[_l1("eng.demo.channel.create.fact_a")],
        existing_items=[],
    )
    assert len(items) == 1
    item = items[0]
    assert item.id == "eng.demo.channel.create.standard_flow"
    assert item.layer == KnowledgeLayer.L2_ENGINEERING_RULE
    assert item.derived_from == ["eng.demo.channel.create.fact_a"]
    assert item.visible_roles == [UserRole.DEVELOPER, UserRole.TEST, UserRole.PRODUCT]


class BadRuleExtractor:
    async def extract(self, facts, existing_rules):
        return EngineeringRuleBatch(
            rules=[
                EngineeringRuleDraft(
                    key="bad",
                    title="Bad",
                    statement="Bad dependency.",
                    derived_from=["eng.demo.channel.create.not_supplied"],
                )
            ]
        )


@pytest.mark.asyncio
async def test_l2_generator_rejects_unknown_l1_dependency() -> None:
    generator = L2Generator(BadRuleExtractor())
    with pytest.raises(ValueError, match="unknown L1 dependency"):
        await generator.generate(
            namespace="demo.channel.create",
            module="demo.channel",
            feature="creation",
            l1_items=[_l1("eng.demo.channel.create.fact_a")],
            existing_items=[],
        )
