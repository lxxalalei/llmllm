from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_real_mattermost_knowledge_item() -> None:
    response = client.get("/api/v1/knowledge/faq.mattermost.channel.create.limit")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "faq.mattermost.channel.create.limit"
    assert payload["status"] == "published"


def test_get_mattermost_lineage_to_code() -> None:
    response = client.get("/api/v1/knowledge/faq.mattermost.channel.create.limit/lineage")
    assert response.status_code == 200
    payload = response.json()
    assert payload["lineage"][0]["id"] == "faq.mattermost.channel.create.limit"
    assert any(
        source["repo"] == "mattermost/mattermost"
        and source["commit"] == "43b2ae87e06b06abe01f9382ec26899c54c31728"
        and source["symbol"] == "CreateChannelWithUser"
        for source in payload["sources"]
    )
