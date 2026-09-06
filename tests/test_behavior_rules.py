import pytest

from app.knowledge.behavior_rules import (
    BehaviorRule,
    BehaviorRuleBatch,
    BehaviorRuleDraft,
    BehaviorRuleGenerator,
    RuleConditions,
    RuleEffect,
    RuleException,
    RulePredicate,
)
from app.knowledge.behavior_views import BehaviorRuleProjector
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus


def _fact(knowledge_id: str) -> KnowledgeItem:
    return KnowledgeItem(
        id=knowledge_id,
        title=knowledge_id,
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="mattermost.channel",
        feature="channel_membership",
        content="Source-backed fact.",
    )


def test_remove_member_rule_projects_one_semantic_source_into_three_views() -> None:
    rule = BehaviorRule(
        id="rule.mattermost.channel.membership.remove_member",
        title="Channel member removal lifecycle",
        domain="channel",
        capability="membership",
        actor="operator",
        action="remove_member",
        resource="channel",
        state_changes=[
            RuleEffect(kind="delete", target="channel_member"),
            RuleEffect(kind="delete", target="channel_thread_memberships"),
        ],
        side_effects=[
            RuleEffect(kind="record", target="leave_history"),
            RuleEffect(kind="websocket", target="user_removed_to_channel"),
            RuleEffect(kind="websocket", target="user_removed_to_removed_user"),
            RuleEffect(kind="plugin_hook", target="UserHasLeftChannel"),
        ],
        source_fact_ids=[
            "eng.mattermost.channel.membership.remove_channel_membership_cleanup",
            "eng.mattermost.channel.membership.remove_user_from_channel_notifications",
        ],
    )

    views = BehaviorRuleProjector().project(
        rule=rule,
        module="mattermost.channel",
        feature="channel_membership",
    )

    assert views.l2.behavior_rule_id == rule.id
    assert views.l3.behavior_rule_id == rule.id
    assert views.l4.behavior_rule_id == rule.id
    assert views.l2.derived_from == rule.source_fact_ids
    assert views.l3.derived_from == [views.l2.id]
    assert views.l4.derived_from == [views.l3.id]
    assert {views.l2.status, views.l3.status, views.l4.status} == {KnowledgeStatus.DRAFT}

    for content in (views.l2.content, views.l3.content, views.l4.content):
        assert "channel member" in content
        assert "channel thread memberships" in content
        assert "user removed to channel" in content
        assert "user removed to removed user" in content


def test_discoverable_self_add_rule_preserves_all_conditions_direction_and_exception() -> None:
    rule = BehaviorRule(
        id="rule.mattermost.channel.membership.discoverable_self_add",
        title="Discoverable private channel self-add",
        domain="channel",
        capability="membership",
        actor="current_user",
        action="add_self_to_channel",
        resource="channel",
        conditions=RuleConditions(
            all=[
                RulePredicate(field="channel.type", operator="equals", value="private"),
                RulePredicate(field="channel.discoverable", operator="equals", value=True),
                RulePredicate(field="channel.policy_enforced", operator="equals", value=False),
                RulePredicate(field="requester_id", operator="equals", value="target_user_id"),
                RulePredicate(field="feature.discoverable_channels", operator="equals", value=True),
            ]
        ),
        decision="reject_direct_add",
        exceptions=[
            RuleException(
                conditions=RuleConditions(
                    all=[
                        RulePredicate(
                            field="requester_id", operator="not_equals", value="target_user_id"
                        )
                    ]
                ),
                outcome="this_rule_does_not_block",
            )
        ],
        source_fact_ids=[
            "eng.mattermost.channel.membership.discoverable_self_add_block",
        ],
    )

    views = BehaviorRuleProjector().project(
        rule=rule,
        module="mattermost.channel",
        feature="channel_membership",
    )

    for content in (views.l2.content, views.l3.content, views.l4.content):
        assert "channel.type equals private" in content
        assert "channel.discoverable equals true" in content
        assert "channel.policy enforced equals false" in content
        assert "requester id equals target_user_id" in content
        assert "feature.discoverable channels equals true" in content
        assert "reject direct add" in content
        assert "requester id not equals target_user_id" in content
        assert "this_rule_does_not_block" in content

    assert "target.is_member" not in views.l2.content
    assert "target.is_member" not in views.l3.content
    assert "target.is_member" not in views.l4.content


class UnknownFactExtractor:
    async def extract(self, facts):
        return BehaviorRuleBatch(
            rules=[
                BehaviorRuleDraft(
                    key="invalid_source",
                    title="Invalid source",
                    domain="channel",
                    capability="membership",
                    actor="user",
                    action="join",
                    resource="channel",
                    source_fact_ids=["eng.missing.fact"],
                )
            ]
        )


@pytest.mark.asyncio
async def test_behavior_rule_generator_rejects_unknown_l1_evidence() -> None:
    generator = BehaviorRuleGenerator(UnknownFactExtractor())

    with pytest.raises(ValueError, match="unknown L1 facts"):
        await generator.generate(
            namespace="mattermost.channel.membership",
            facts=[_fact("eng.mattermost.channel.membership.real_fact")],
        )
