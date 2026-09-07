from pathlib import Path

import yaml

from app.knowledge import BehaviorRule, KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus


RULE_ROOT = Path("knowledge/behavior-rules/mattermost")


def _rule_ids() -> set[str]:
    return {
        BehaviorRule.model_validate(yaml.safe_load(path.read_text(encoding="utf-8"))).id
        for path in RULE_ROOT.rglob("*.yaml")
    }


def test_mattermost_channel_behavior_rules_are_grounded_and_have_core_views() -> None:
    catalog = KnowledgeCatalog.from_directory("knowledge")
    rule_files = sorted(RULE_ROOT.rglob("*.yaml"))

    assert rule_files

    seen_rule_ids: set[str] = set()
    for path in rule_files:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        rule = BehaviorRule.model_validate(payload)

        assert rule.id not in seen_rule_ids
        seen_rule_ids.add(rule.id)

        for fact_id in rule.source_fact_ids:
            fact = catalog.get(fact_id)
            assert fact.layer == KnowledgeLayer.L1_ENGINEERING_FACT
            assert fact.status in {KnowledgeStatus.REVIEW, KnowledgeStatus.PUBLISHED}
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
        assert {item.layer for item in views if item.layer != KnowledgeLayer.L4_USER_KNOWLEDGE} == {
            KnowledgeLayer.L2_ENGINEERING_RULE,
            KnowledgeLayer.L3_PRODUCT_LOGIC,
        }
        assert all(
            item.status in {KnowledgeStatus.REVIEW, KnowledgeStatus.PUBLISHED}
            for item in views
        )


def test_l4_behavior_rule_links_resolve_when_present() -> None:
    catalog = KnowledgeCatalog.from_directory("knowledge")
    rule_ids = _rule_ids()

    for item in catalog._items.values():
        if item.layer != KnowledgeLayer.L4_USER_KNOWLEDGE:
            continue
        for rule_id in item.linked_behavior_rule_ids:
            assert rule_id in rule_ids


def test_coarse_channel_rules_are_replaced_by_atomic_decisions() -> None:
    rule_ids = _rule_ids()
    removed_coarse_ids = {
        "rule.mattermost.channel.membership.add_permission_split",
        "rule.mattermost.channel.creation.create_permission_gate",
        "rule.mattermost.channel.membership.add_integrity_constraints",
        "rule.mattermost.channel.update.property_permission_by_type",
        "rule.mattermost.channel.update.privacy_conversion",
        "rule.mattermost.channel.archive_restore.archive_permission_and_default",
    }
    required_atomic_ids = {
        "rule.mattermost.channel.membership.open_self_add_permission",
        "rule.mattermost.channel.membership.open_add_other_permission",
        "rule.mattermost.channel.membership.private_add_permission",
        "rule.mattermost.channel.membership.direct_group_add_rejected",
        "rule.mattermost.channel.creation.create_open_permission",
        "rule.mattermost.channel.creation.create_private_permission",
        "rule.mattermost.channel.creation.standard_create_required_fields",
        "rule.mattermost.channel.creation.standard_create_type_boundary",
        "rule.mattermost.channel.membership.team_member_integrity",
        "rule.mattermost.channel.membership.member_add_type_boundary",
        "rule.mattermost.channel.membership.group_constrained_membership",
        "rule.mattermost.channel.membership.member_add_guarded_hook",
        "rule.mattermost.channel.update.open_property_permission",
        "rule.mattermost.channel.update.private_property_permission",
        "rule.mattermost.channel.update.direct_group_limited_update",
        "rule.mattermost.channel.update.unsupported_property_update_type",
        "rule.mattermost.channel.update.public_to_private_conversion",
        "rule.mattermost.channel.update.private_to_public_conversion",
        "rule.mattermost.channel.update.space_privacy_conversion_rejected",
        "rule.mattermost.channel.archive_restore.open_archive_permission",
        "rule.mattermost.channel.archive_restore.private_archive_permission",
        "rule.mattermost.channel.archive_restore.already_archived_rejected",
        "rule.mattermost.channel.archive_restore.town_square_archive_rejected",
        "rule.mattermost.channel.archive_restore.standard_archive_type_boundary",
    }

    assert removed_coarse_ids.isdisjoint(rule_ids)
    assert required_atomic_ids <= rule_ids


def test_user_intent_assets_link_only_the_rules_needed_for_the_question() -> None:
    catalog = KnowledgeCatalog.from_directory("knowledge")
    expected_links = {
        "faq.mattermost.channel.membership.self_vs_add_other_permission": {
            "rule.mattermost.channel.membership.open_self_add_permission",
            "rule.mattermost.channel.membership.open_add_other_permission",
        },
        "faq.mattermost.channel.membership.add_integrity_constraints": {
            "rule.mattermost.channel.membership.team_member_integrity",
            "rule.mattermost.channel.membership.group_constrained_membership",
        },
        "faq.mattermost.channel.creation.create_permission_gate": {
            "rule.mattermost.channel.creation.create_open_permission",
            "rule.mattermost.channel.creation.create_private_permission",
            "rule.mattermost.channel.creation.standard_create_type_boundary",
        },
        "faq.mattermost.channel.update.property_permission_by_type": {
            "rule.mattermost.channel.update.open_property_permission",
            "rule.mattermost.channel.update.private_property_permission",
            "rule.mattermost.channel.update.direct_group_limited_update",
        },
        "faq.mattermost.channel.update.privacy_conversion": {
            "rule.mattermost.channel.update.private_to_public_conversion",
        },
        "faq.mattermost.channel.archive_restore.archive_permission_and_default": {
            "rule.mattermost.channel.archive_restore.town_square_archive_rejected",
            "rule.mattermost.channel.archive_restore.open_archive_permission",
            "rule.mattermost.channel.archive_restore.private_archive_permission",
        },
    }

    for knowledge_id, expected in expected_links.items():
        assert set(catalog.get(knowledge_id).linked_behavior_rule_ids) == expected


def test_guarded_hooks_are_explicit_in_behavior_rules() -> None:
    rules = {}
    for path in RULE_ROOT.rglob("*.yaml"):
        rule = BehaviorRule.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
        rules[rule.id] = rule

    update_targets = {
        effect.target
        for effect in rules[
            "rule.mattermost.channel.update.generic_update_guard_and_event"
        ].side_effects
        if effect.kind == "plugin_guard"
    }
    restore_targets = {
        effect.target
        for effect in rules[
            "rule.mattermost.channel.archive_restore.restore_permission_and_guard"
        ].side_effects
        if effect.kind == "plugin_guard"
    }

    assert update_targets == {"ChannelWillBeUpdated"}
    assert restore_targets == {"ChannelWillBeRestored"}
