from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.views import drill_down, role_allows, visible_items
from app.main import app

client = TestClient(app)

LIMIT_FAQ = "faq.mattermost.channel.create.limit"
TEAM_CHANNEL_L3 = "product.mattermost.channel.create.team_channel"
MANAGED_L3 = "product.mattermost.channel.create.managed_category"
SPACE_DRAFT_L4 = "faq.mattermost.channel.create.space_unavailable"
STANDARD_FLOW_L2 = "eng.mattermost.channel.create.standard_flow"
TEAM_LIMIT_L1 = "eng.mattermost.channel.create.team_limit"


@pytest.fixture(scope="module")
def catalog() -> KnowledgeCatalog:
    return KnowledgeCatalog.from_directory(Path("knowledge"))


def _item(catalog: KnowledgeCatalog, knowledge_id: str):
    return catalog.get(knowledge_id)


def test_user_sees_only_published_l3_l4_where_user_is_authorized(catalog) -> None:
    visible = visible_items(list(catalog._items.values()), UserRole.USER)
    assert any(item.id == LIMIT_FAQ for item in visible)
    # boundary: no draft L4, no review L3, no L3 without user in visible_roles
    assert all(
        item.status == KnowledgeStatus.PUBLISHED
        and item.layer in (KnowledgeLayer.L3_PRODUCT_LOGIC, KnowledgeLayer.L4_USER_KNOWLEDGE)
        and UserRole.USER in item.visible_roles
        for item in visible
    )
    assert not role_allows(UserRole.USER, _item(catalog, SPACE_DRAFT_L4))
    assert not role_allows(UserRole.USER, _item(catalog, TEAM_CHANNEL_L3))
    assert not role_allows(UserRole.USER, _item(catalog, MANAGED_L3))
    assert not role_allows(UserRole.USER, _item(catalog, STANDARD_FLOW_L2))
    assert not role_allows(UserRole.USER, _item(catalog, TEAM_LIMIT_L1))


def test_product_and_test_layer_boundaries(catalog) -> None:
    # product: L3/L2 for review and product work; L1 is developer/test-only in assets
    assert role_allows(UserRole.PRODUCT, _item(catalog, TEAM_CHANNEL_L3))
    assert role_allows(UserRole.PRODUCT, _item(catalog, MANAGED_L3))  # review visible for review work
    assert role_allows(UserRole.PRODUCT, _item(catalog, STANDARD_FLOW_L2))
    assert not role_allows(UserRole.PRODUCT, _item(catalog, TEAM_LIMIT_L1))
    # test: same as product, plus L1 engineering facts (test needs code detail)
    assert role_allows(UserRole.TEST, _item(catalog, TEAM_LIMIT_L1))


def test_developer_sees_l1_l2_and_published_upper_layers(catalog) -> None:
    assert role_allows(UserRole.DEVELOPER, _item(catalog, TEAM_LIMIT_L1))
    assert role_allows(UserRole.DEVELOPER, _item(catalog, STANDARD_FLOW_L2))
    assert role_allows(UserRole.DEVELOPER, _item(catalog, TEAM_CHANNEL_L3))
    assert role_allows(UserRole.DEVELOPER, _item(catalog, LIMIT_FAQ))


def test_drill_lower_boundaries(catalog) -> None:
    l3 = _item(catalog, TEAM_CHANNEL_L3)
    # product drills L3 -> L2
    parents = drill_down(catalog, l3, UserRole.PRODUCT)
    assert len(parents) == 2
    assert all(item.layer == KnowledgeLayer.L2_ENGINEERING_RULE for item in parents)
    # user cannot drill into L3 (not authorized) even when published
    assert drill_down(catalog, l3, UserRole.USER) == []
    # developer drilling an L4 FAQ reaches the published L3
    faq = _item(catalog, LIMIT_FAQ)
    assert [p.id for p in drill_down(catalog, faq, UserRole.DEVELOPER)] == [TEAM_CHANNEL_L3]
    assert drill_down(catalog, faq, UserRole.USER) == []


def test_developer_locates_pinned_code_via_l1(catalog) -> None:
    l1 = _item(catalog, TEAM_LIMIT_L1)
    assert role_allows(UserRole.DEVELOPER, l1)
    assert len(l1.sources) == 1
    source = l1.sources[0]
    assert source.repo == "mattermost/mattermost"
    assert source.commit == "43b2ae87e06b06abe01f9382ec26899c54c31728"
    assert source.file == "server/channels/app/channel.go"
    assert source.symbol in ("CreateChannelWithUser", "CreateChannel")
    # manual assets bind repo/commit/file/symbol; line ranges are optional here
    assert source.start_line is None or isinstance(source.start_line, int)


def test_api_list_role_user_returns_only_published_user_knowledge() -> None:
    response = client.get("/api/v1/knowledge", params={"role": "user"})
    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == LIMIT_FAQ for item in payload)
    ids = {item["id"] for item in payload}
    assert SPACE_DRAFT_L4 not in ids
    assert TEAM_CHANNEL_L3 not in ids
    assert MANAGED_L3 not in ids
    assert all(item["status"] == "published" for item in payload)


def test_api_detail_enforces_role_visibility() -> None:
    assert client.get(f"/api/v1/knowledge/{LIMIT_FAQ}", params={"role": "user"}).status_code == 200
    # forbidden to a role -> indistinguishable 404 (no enumeration)
    assert client.get(f"/api/v1/knowledge/{TEAM_CHANNEL_L3}", params={"role": "user"}).status_code == 404
    assert client.get(f"/api/v1/knowledge/{MANAGED_L3}", params={"role": "user"}).status_code == 404
    assert client.get(f"/api/v1/knowledge/{MANAGED_L3}", params={"role": "product"}).status_code == 200
    assert client.get(f"/api/v1/knowledge/{LIMIT_FAQ}", params={"role": "bogus"}).status_code == 422


def test_api_lineage_and_drill_enforce_role() -> None:
    ok = client.get(f"/api/v1/knowledge/{LIMIT_FAQ}/lineage", params={"role": "user"})
    assert ok.status_code == 200
    hidden = client.get(f"/api/v1/knowledge/{TEAM_CHANNEL_L3}/lineage", params={"role": "user"})
    assert hidden.status_code == 404
    drill = client.get(
        f"/api/v1/knowledge/{TEAM_CHANNEL_L3}/drill", params={"role": "product"}
    )
    assert drill.status_code == 200
    items = drill.json()
    assert len(items) == 2
    assert all(item["layer"] == "L2" for item in items)
    assert client.get(
        f"/api/v1/knowledge/{TEAM_CHANNEL_L3}/drill", params={"role": "user"}
    ).status_code == 404
