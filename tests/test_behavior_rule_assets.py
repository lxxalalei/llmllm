from pathlib import Path

import yaml

from app.knowledge import BehaviorRule, KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus


RULE_ROOT = Path("knowledge/behavior-rules/mattermost")


def test_mattermost_channel_behavior_rules_are_grounded_and_have_role_views() -> None:
    catalog = KnowledgeCatalog.from_directory("knowledge")
    rule_files = sorted(RULE_ROOT.rglob("*.yaml"))

    assert len(rule_files) == 20

    seen_rule_ids: set[str] = set()
    for path in rule_files:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        rule = BehaviorRule.model_validate(payload)

        assert rule.id not in seen_rule_ids
        seen_rule_ids.add(rule.id)

        for fact_id in rule.source_fact_ids:
            fact = catalog.get(fact_id)
            assert fact.layer == KnowledgeLayer.L1_ENGINEERING_FACT
            assert fact.status == KnowledgeStatus.REVIEW
            assert fact.sources
            assert all(
                source.repo == "mattermost/mattermost"
                and source.file
                and source.symbol
                for source in fact.sources
            )

        views = [
            item
            for item in catalog._items.values()
            if item.behavior_rule_id == rule.id
        ]
        assert {item.layer for item in views} == {
            KnowledgeLayer.L2_ENGINEERING_RULE,
            KnowledgeLayer.L3_PRODUCT_LOGIC,
            KnowledgeLayer.L4_USER_KNOWLEDGE,
        }
        assert all(item.status == KnowledgeStatus.REVIEW for item in views)
