from __future__ import annotations

from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole

LAYER_ORDER = {
    KnowledgeLayer.L1_ENGINEERING_FACT: 1,
    KnowledgeLayer.L2_ENGINEERING_RULE: 2,
    KnowledgeLayer.L3_PRODUCT_LOGIC: 3,
    KnowledgeLayer.L4_USER_KNOWLEDGE: 4,
}


def role_allows(
    role: UserRole,
    item: KnowledgeItem,
    *,
    include_unpublished: bool = False,
) -> bool:
    """Role consumption boundary.

    Normal serve mode only consumes Published assets for every role. Review
    tooling must opt in with ``include_unpublished=True``; role visibility still
    applies, but Draft/Review/Outdated assets can then be inspected explicitly.
    """
    if role not in item.visible_roles:
        return False
    if not include_unpublished and item.status != KnowledgeStatus.PUBLISHED:
        return False
    if role == UserRole.USER:
        return item.layer in (
            KnowledgeLayer.L3_PRODUCT_LOGIC,
            KnowledgeLayer.L4_USER_KNOWLEDGE,
        )
    return True


def visible_items(
    items: list[KnowledgeItem],
    role: UserRole,
    *,
    include_unpublished: bool = False,
) -> list[KnowledgeItem]:
    return [
        item
        for item in items
        if role_allows(role, item, include_unpublished=include_unpublished)
    ]


def drill_down(catalog, item: KnowledgeItem, role: UserRole | None = None) -> list[KnowledgeItem]:
    """Direct derived_from items on a strictly lower layer.

    role=None is the unfiltered management/review view; otherwise normal serve
    visibility applies.
    """
    parents: list[KnowledgeItem] = []
    for parent_id in item.derived_from:
        try:
            parent = catalog.get(parent_id)
        except KeyError:
            continue
        if LAYER_ORDER[parent.layer] >= LAYER_ORDER[item.layer]:
            continue
        if role is not None and not role_allows(role, parent):
            continue
        parents.append(parent)
    return parents
