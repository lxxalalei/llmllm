from __future__ import annotations

from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole

LAYER_ORDER = {
    KnowledgeLayer.L1_ENGINEERING_FACT: 1,
    KnowledgeLayer.L2_ENGINEERING_RULE: 2,
    KnowledgeLayer.L3_PRODUCT_LOGIC: 3,
    KnowledgeLayer.L4_USER_KNOWLEDGE: 4,
}


def role_allows(role: UserRole, item: KnowledgeItem) -> bool:
    """Role consumption boundary.

    - USER: only Published L3/L4 and only where the asset grants the user role.
    - PRODUCT / TEST / DEVELOPER: anything their asset-level visible_roles grant
      (L2/L3 for product/test including review items; L1/L2 for developers), so
      review work and code location stay possible. Deprecated handling is a
      consumption-policy decision for later phases.
    """
    if role not in item.visible_roles:
        return False
    if role == UserRole.USER:
        return item.layer in (
            KnowledgeLayer.L3_PRODUCT_LOGIC,
            KnowledgeLayer.L4_USER_KNOWLEDGE,
        ) and item.status == KnowledgeStatus.PUBLISHED
    return True


def visible_items(items: list[KnowledgeItem], role: UserRole) -> list[KnowledgeItem]:
    return [item for item in items if role_allows(role, item)]


def drill_down(catalog, item: KnowledgeItem, role: UserRole | None = None) -> list[KnowledgeItem]:
    """Direct derived_from items on a strictly lower layer.

    role=None is the unfiltered management view; otherwise the role
    consumption boundary applies.
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
