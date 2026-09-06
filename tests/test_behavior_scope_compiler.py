from pathlib import Path

import pytest

from app.knowledge.batch_compiler import BatchKnowledgeScope, compile_scope_preview
from app.knowledge.behavior_rules import (
    BehaviorRuleBatch,
    BehaviorRuleDraft,
    BehaviorRuleGenerator,
    RuleEffect,
)
from app.knowledge.behavior_views import BehaviorRuleProjector
from app.knowledge.domain import KnowledgeDomainManifest, summarize_domain_previews
from app.knowledge.l1_generator import EngineeringFactBatch, EngineeringFactDraft, L1Generator


class FactExtractor:
    async def extract(self, symbols):
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="remove_member_cleanup",
                    symbol=symbols[0].name,
                    title="Member cleanup",
                    statement="Removing a member deletes membership state.",
                )
            ]
        )


class RuleExtractor:
    async def extract(self, facts):
        return BehaviorRuleBatch(
            rules=[
                BehaviorRuleDraft(
                    key="remove_member",
                    title="Remove member lifecycle",
                    domain="channel",
                    capability="membership",
                    actor="operator",
                    action="remove_member",
                    resource="channel",
                    state_changes=[RuleEffect(kind="delete", target="channel_member")],
                    source_fact_ids=[facts[0].id],
                )
            ]
        )


@pytest.mark.asyncio
async def test_behavior_rule_scope_compiles_l1_into_three_views_without_l2_generator(
    tmp_path: Path,
) -> None:
    (tmp_path / "channel.go").write_text(
        "package channel\nfunc RemoveMember() {}\n", encoding="utf-8"
    )
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.channel.membership",
            "module": "demo.channel",
            "feature": "channel_membership",
            "pipeline": "behavior_rule",
            "propagation": "review",
            "sources": [{"path": "channel.go", "symbols": ["RemoveMember"]}],
        }
    )

    preview = await compile_scope_preview(
        repository_root=tmp_path,
        commit="snapshot",
        scope=scope,
        l1_generator=L1Generator(FactExtractor()),
        behavior_rule_generator=BehaviorRuleGenerator(RuleExtractor()),
        behavior_projector=BehaviorRuleProjector(),
    )

    assert preview["coverage"] == {
        "source_files": 1,
        "symbols": 1,
        "l1": 1,
        "l2": 1,
        "behavior_rules": 1,
        "l3": 1,
        "l4": 1,
    }
    rule_id = preview["behavior_rules"][0]["id"]
    assert preview["l2_items"][0]["behavior_rule_id"] == rule_id
    assert preview["l3_items"][0]["behavior_rule_id"] == rule_id
    assert preview["l4_items"][0]["behavior_rule_id"] == rule_id
    assert preview["l2_items"][0]["status"] == "draft"
    assert preview["l3_items"][0]["status"] == "draft"
    assert preview["l4_items"][0]["status"] == "draft"


def test_behavior_rule_scope_does_not_allow_auto_publish() -> None:
    with pytest.raises(ValueError, match="produces reviewable drafts"):
        BatchKnowledgeScope.model_validate(
            {
                "repo": "demo/repo",
                "namespace": "demo.channel",
                "module": "demo.channel",
                "feature": "channel_update",
                "pipeline": "behavior_rule",
                "propagation": "auto_publish",
                "sources": [{"path": "channel.go", "symbols": ["Update"]}],
            }
        )


def test_domain_summary_reports_feature_and_total_coverage() -> None:
    manifest = KnowledgeDomainManifest(
        id="mattermost.channel",
        module="mattermost.channel",
        scopes=["creation.json", "membership.json"],
    )
    previews = [
        {
            "scope": {
                "module": "mattermost.channel",
                "feature": "channel_creation",
                "pipeline": "behavior_rule",
            },
            "coverage": {
                "source_files": 2,
                "symbols": 3,
                "l1": 8,
                "behavior_rules": 4,
                "l2": 4,
                "l3": 4,
                "l4": 4,
            },
        },
        {
            "scope": {
                "module": "mattermost.channel",
                "feature": "channel_membership",
                "pipeline": "behavior_rule",
            },
            "coverage": {
                "source_files": 4,
                "symbols": 12,
                "l1": 20,
                "behavior_rules": 7,
                "l2": 7,
                "l3": 7,
                "l4": 7,
            },
        },
    ]

    summary = summarize_domain_previews(manifest, previews)

    assert summary["scope_count"] == 2
    assert summary["coverage"] == {
        "source_files": 6,
        "symbols": 15,
        "l1": 28,
        "behavior_rules": 11,
        "l2": 11,
        "l3": 11,
        "l4": 11,
    }
