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


def test_developer_lineage_keeps_engineering_layers_and_code_sources() -> None:
    response = client.get(
        f"/api/v1/knowledge/{LIMIT_FAQ}/lineage",
        params={"role": "developer"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert any(item["layer"] == "L1" for item in payload["lineage"])
    assert any(source["repo"] == "mattermost/mattermost" for source in payload["sources"])
