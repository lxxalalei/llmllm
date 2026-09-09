"""Role visibility contracts: synthetic unit fixtures + dynamic real-asset API checks."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.knowledge.assets import KnowledgeCatalog
from app.knowledge.models import KnowledgeItem, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.views import drill_down, role_allows, visible_items
from app.main import app

client = TestClient(app)

ALL = [UserRole.USER, UserRole.PRODUCT, UserRole.TEST, UserRole.DEVELOPER, UserRole.ADMIN]
L3_ROLES = [UserRole.PRODUCT, UserRole.TEST, UserRole.DEVELOPER, UserRole.ADMIN]
L2_ROLES = L3_ROLES
L1_ROLES = [UserRole.DEVELOPER, UserRole.TEST]


def _item(knowledge_id: str, layer, status, roles, derived_from=None) -> KnowledgeItem:
    return KnowledgeItem(
        id=knowledge_id,
        title=knowledge_id,
        layer=layer,
        module="mattermost.channel",
        feature="channel_permission",
        content="Permission rule text.",
        status=status,
        derived_from=list(derived_from or []),
        visible_roles=list(roles),
    )


def _catalog():
    items = [
        _item("eng.c.permission.fact", KnowledgeLayer.L1_ENGINEERING_FACT, KnowledgeStatus.PUBLISHED, L1_ROLES),
        _item("eng.c.permission.rule", KnowledgeLayer.L2_ENGINEERING_RULE, KnowledgeStatus.PUBLISHED, L2_ROLES,
              derived_from=["eng.c.permission.fact"]),
        _item("eng.c.permission.rule_old", KnowledgeLayer.L2_ENGINEERING_RULE, KnowledgeStatus.REVIEW, L2_ROLES),
        _item("product.c.permission.rule", KnowledgeLayer.L3_PRODUCT_LOGIC, KnowledgeStatus.PUBLISHED, L3_ROLES,
              derived_from=["eng.c.permission.rule"]),
        _item("product.c.permission.rule_review", KnowledgeLayer.L3_PRODUCT_LOGIC, KnowledgeStatus.REVIEW, L3_ROLES),
        _item("faq.c.permission.rule", KnowledgeLayer.L4_USER_KNOWLEDGE, KnowledgeStatus.PUBLISHED, ALL,
              derived_from=["product.c.permission.rule"]),
        _item("faq.c.permission.rule_review", KnowledgeLayer.L4_USER_KNOWLEDGE, KnowledgeStatus.REVIEW, ALL),
        _item("faq.c.permission.old", KnowledgeLayer.L4_USER_KNOWLEDGE, KnowledgeStatus.DEPRECATED, ALL),
    ]
    return KnowledgeCatalog(items)


@pytest.fixture(scope="module")
def synthetic() -> KnowledgeCatalog:
    return _catalog()


@pytest.fixture(scope="module")
def real() -> KnowledgeCatalog:
    return KnowledgeCatalog.from_directory(Path("knowledge"))


def test_user_serve_sees_only_published_l3_l4_with_user_role(synthetic) -> None:
    visible = visible_items(list(synthetic._items.values()), UserRole.USER)
    visible_ids = {item.id for item in visible}
    assert visible_ids == {"faq.c.permission.rule"}
    assert all(
        item.status == KnowledgeStatus.PUBLISHED
        and item.layer in (KnowledgeLayer.L3_PRODUCT_LOGIC, KnowledgeLayer.L4_USER_KNOWLEDGE)
        for item in visible
    )
    # user can never consume a role-restricted L3
    assert not role_allows(UserRole.USER, synthetic.get("product.c.permission.rule"))


def test_product_normal_serve_uses_published_role_assets(synthetic) -> None:
    assert role_allows(UserRole.PRODUCT, synthetic.get("product.c.permission.rule"))
    assert role_allows(UserRole.PRODUCT, synthetic.get("eng.c.permission.rule"))
    assert not role_allows(UserRole.PRODUCT, synthetic.get("eng.c.permission.fact"))
    assert not role_allows(UserRole.PRODUCT, synthetic.get("product.c.permission.rule_review"))
    assert not role_allows(UserRole.PRODUCT, synthetic.get("eng.c.permission.rule_old"))
    assert role_allows(UserRole.TEST, synthetic.get("eng.c.permission.fact"))


def test_review_mode_explicitly_allows_unpublished_role_assets(synthetic) -> None:
    assert role_allows(UserRole.PRODUCT, synthetic.get("product.c.permission.rule_review"), include_unpublished=True)
    assert role_allows(UserRole.PRODUCT, synthetic.get("eng.c.permission.rule_old"), include_unpublished=True)
    assert not role_allows(UserRole.PRODUCT, synthetic.get("eng.c.permission.fact"), include_unpublished=True)
    assert role_allows(UserRole.TEST, synthetic.get("eng.c.permission.fact"), include_unpublished=True)
    assert role_allows(UserRole.DEVELOPER, synthetic.get("product.c.permission.rule"))


def test_developer_serve_and_review_boundaries(synthetic) -> None:
    assert role_allows(UserRole.DEVELOPER, synthetic.get("eng.c.permission.fact"))
    assert not role_allows(UserRole.DEVELOPER, synthetic.get("eng.c.permission.rule_old"))
    assert role_allows(UserRole.DEVELOPER, synthetic.get("eng.c.permission.rule_old"), include_unpublished=True)
    assert not role_allows(UserRole.DEVELOPER, synthetic.get("faq.c.permission.rule_review"))
    assert role_allows(UserRole.DEVELOPER, synthetic.get("faq.c.permission.rule_review"), include_unpublished=True)


def test_drill_down_respects_role_layer_and_status(synthetic) -> None:
    faq = synthetic.get("faq.c.permission.rule")
    # L3 parent is not visible to user role -> user drill is empty
    assert drill_down(synthetic, faq, UserRole.USER) == []
    # developer can follow the published chain down to L3
    parents = drill_down(synthetic, faq, UserRole.DEVELOPER)
    assert [p.id for p in parents] == ["product.c.permission.rule"]
    # product drills from L3 to published L2 only (review L2 stays hidden)
    l3 = synthetic.get("product.c.permission.rule")
    assert [p.id for p in drill_down(synthetic, l3, UserRole.PRODUCT)] == ["eng.c.permission.rule"]


def test_real_api_user_list_and_detail_visibility(real) -> None:
    pub_l4 = next(i.id for i in real._items.values()
                  if i.status == KnowledgeStatus.PUBLISHED and i.layer == KnowledgeLayer.L4_USER_KNOWLEDGE
                  and UserRole.USER in i.visible_roles)
    dep_l4 = next((i.id for i in real._items.values()
                   if i.status == KnowledgeStatus.DEPRECATED and i.layer == KnowledgeLayer.L4_USER_KNOWLEDGE
                   and UserRole.USER in i.visible_roles), None)
    pub_l3_hidden = next(i.id for i in real._items.values()
                         if i.status == KnowledgeStatus.PUBLISHED and i.layer == KnowledgeLayer.L3_PRODUCT_LOGIC
                         and UserRole.USER not in i.visible_roles and UserRole.PRODUCT in i.visible_roles)
    payload = client.get("/api/v1/knowledge", params={"role": "user"}).json()
    ids = {item["id"] for item in payload}
    assert pub_l4 in ids
    assert pub_l3_hidden not in ids
    if dep_l4 is not None:
        assert dep_l4 not in ids
    assert all(item["status"] == "published" for item in payload)
    assert client.get(f"/api/v1/knowledge/{pub_l4}", params={"role": "user"}).status_code == 200
    assert client.get(f"/api/v1/knowledge/{pub_l3_hidden}", params={"role": "user"}).status_code == 404
    if dep_l4 is not None:
        assert client.get(f"/api/v1/knowledge/{dep_l4}", params={"role": "user"}).status_code == 404
    assert client.get(f"/api/v1/knowledge/{pub_l3_hidden}", params={"role": "product"}).status_code == 200
    assert client.get(f"/api/v1/knowledge/{pub_l4}", params={"role": "bogus"}).status_code == 422


def test_real_api_lineage_and_drill_enforce_serve_visibility(real) -> None:
    pub_l4 = next(i.id for i in real._items.values()
                  if i.status == KnowledgeStatus.PUBLISHED and i.layer == KnowledgeLayer.L4_USER_KNOWLEDGE
                  and UserRole.USER in i.visible_roles)
    pub_l3_hidden = next(i.id for i in real._items.values()
                         if i.status == KnowledgeStatus.PUBLISHED and i.layer == KnowledgeLayer.L3_PRODUCT_LOGIC
                         and UserRole.USER not in i.visible_roles and UserRole.PRODUCT in i.visible_roles)
    assert client.get(f"/api/v1/knowledge/{pub_l4}/lineage", params={"role": "user"}).status_code == 200
    assert client.get(f"/api/v1/knowledge/{pub_l3_hidden}/lineage", params={"role": "user"}).status_code == 404
    drill = client.get(f"/api/v1/knowledge/{pub_l3_hidden}/drill", params={"role": "product"})
    assert drill.status_code == 200
    for parent in drill.json():
        item = real.get(parent["id"])
        assert role_allows(UserRole.PRODUCT, item), f"{parent['id']} should be visible to product in serve mode"
        assert item.status == KnowledgeStatus.PUBLISHED
    assert client.get(f"/api/v1/knowledge/{pub_l3_hidden}/drill", params={"role": "user"}).status_code == 404
