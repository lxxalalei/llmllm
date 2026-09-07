from __future__ import annotations

from pydantic import BaseModel

from app.knowledge.behavior_rules import BehaviorRule, RuleConditions, RuleEffect, RulePredicate
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole


class BehaviorRuleViews(BaseModel):
    l2: KnowledgeItem
    l3: KnowledgeItem
    l4: KnowledgeItem | None = None


def _display_field(value: str) -> str:
    return value.replace("_", " ")


def _display_value(value: object | None) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _predicate_text(predicate: RulePredicate) -> str:
    field = _display_field(predicate.field)
    operator = predicate.operator.replace("_", " ")
    value = _display_value(predicate.value)
    return f"{field} {operator}" + (f" {value}" if value else "")


def _conditions_text(conditions: RuleConditions) -> str:
    parts: list[str] = []
    if conditions.all:
        parts.append("all of: " + "; ".join(_predicate_text(item) for item in conditions.all))
    if conditions.any:
        parts.append("any of: " + "; ".join(_predicate_text(item) for item in conditions.any))
    return " | ".join(parts)


def _effect_text(effect: RuleEffect) -> str:
    base = f"{effect.kind.replace('_', ' ')} {effect.target.replace('_', ' ')}"
    if effect.detail:
        return f"{base} ({effect.detail})"
    return base


def _rule_suffix(rule: BehaviorRule) -> str:
    return rule.id.removeprefix("rule.")


def _engineering_content(rule: BehaviorRule) -> str:
    lines = [f"Actor `{rule.actor}` performs `{rule.action}` on `{rule.resource}`."]
    conditions = _conditions_text(rule.conditions)
    if conditions:
        lines.append(f"Conditions: {conditions}.")
    if rule.decision:
        lines.append(f"Decision: `{rule.decision}`.")
    if rule.state_changes:
        lines.append("State changes: " + "; ".join(_effect_text(item) for item in rule.state_changes) + ".")
    if rule.side_effects:
        lines.append("Side effects: " + "; ".join(_effect_text(item) for item in rule.side_effects) + ".")
    if rule.exceptions:
        rendered = [
            f"{_conditions_text(exception.conditions)} => {exception.outcome}"
            for exception in rule.exceptions
        ]
        lines.append("Exceptions: " + "; ".join(rendered) + ".")
    return "\n\n".join(lines)


def _product_content(rule: BehaviorRule) -> str:
    subject = _display_field(rule.actor)
    action = _display_field(rule.action)
    resource = _display_field(rule.resource)
    lines = [f"{subject} performs {action} on {resource} under the rule \"{rule.title}\"."]
    conditions = _conditions_text(rule.conditions)
    if conditions:
        lines.append(f"This applies when {conditions}.")
    if rule.decision:
        lines.append(f"The resulting behavior is {rule.decision.replace('_', ' ')}.")
    if rule.state_changes:
        lines.append("The system changes: " + "; ".join(_effect_text(item) for item in rule.state_changes) + ".")
    if rule.side_effects:
        lines.append("The system also triggers: " + "; ".join(_effect_text(item) for item in rule.side_effects) + ".")
    if rule.exceptions:
        rendered = [
            f"when {_conditions_text(exception.conditions)}, {exception.outcome}"
            for exception in rule.exceptions
        ]
        lines.append("Exceptions: " + "; ".join(rendered) + ".")
    return "\n\n".join(lines)


class BehaviorRuleProjector:
    """Create engineering/product views from one structured rule.

    L4 is deliberately excluded. User knowledge is organized by user intent
    and may reference zero, one, or multiple BehaviorRules.
    """

    def project(self, *, rule: BehaviorRule, module: str, feature: str) -> BehaviorRuleViews:
        suffix = _rule_suffix(rule)
        l2 = KnowledgeItem(
            id=f"eng.{suffix}.behavior",
            title=rule.title,
            layer=KnowledgeLayer.L2_ENGINEERING_RULE,
            module=module,
            feature=feature,
            content=_engineering_content(rule),
            status=KnowledgeStatus.DRAFT,
            derived_from=rule.source_fact_ids,
            behavior_rule_id=rule.id,
            visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
        )
        l3 = KnowledgeItem(
            id=f"product.{suffix}",
            title=rule.title,
            layer=KnowledgeLayer.L3_PRODUCT_LOGIC,
            module=module,
            feature=feature,
            content=_product_content(rule),
            status=KnowledgeStatus.DRAFT,
            derived_from=[l2.id],
            behavior_rule_id=rule.id,
            visible_roles=[UserRole.PRODUCT, UserRole.TEST, UserRole.DEVELOPER, UserRole.ADMIN],
        )
        return BehaviorRuleViews(l2=l2, l3=l3)
