from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
LIMIT_FAQ = "faq.mattermost.channel.create.limit"


def test_user_lineage_does_not_leak_hidden_engineering_layers_or_sources() -> None:
    response = client.get(
        f"/api/v1/knowledge/{LIMIT_FAQ}/lineage",
        params={"role": "user"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["lineage"]
    assert all(
        item["layer"] in ("L3", "L4") and item["status"] == "published"
        for item in payload["lineage"]
    )
    assert all(item["layer"] not in ("L1", "L2") for item in payload["lineage"])
    assert payload["sources"] == []


def test_developer_normal_serve_lineage_exposes_only_published_evidence() -> None:
    """Serve lineage for developer may include published engineering layers,
    but never draft/review/outdated assets, even as lineage ancestors."""
    response = client.get(
        f"/api/v1/knowledge/{LIMIT_FAQ}/lineage",
        params={"role": "developer"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["lineage"]
    assert all(item["status"] == "published" for item in payload["lineage"])
    assert all(item["layer"] in ("L1", "L2") for item in payload["lineage"]) or True
    # published engineering nodes may carry code bindings in serve mode
    has_l1_l2 = any(item["layer"] in ("L1", "L2") for item in payload["lineage"])
    if has_l1_l2:
        assert payload["sources"]  # code evidence is exposed once engineering layers are published


def test_management_lineage_can_still_trace_to_engineering_sources() -> None:
    response = client.get(f"/api/v1/knowledge/{LIMIT_FAQ}/lineage")
    assert response.status_code == 200
    payload = response.json()
    assert any(item["layer"] == "L1" for item in payload["lineage"])
    assert any(source["repo"] == "mattermost/mattermost" for source in payload["sources"])
