from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _payload(before: str = "1" * 40, after: str = "2" * 40) -> dict:
    return {
        "before": before,
        "after": after,
        "repository": {"full_name": "mattermost/mattermost"},
    }


def test_github_webhook_requires_event_header() -> None:
    response = client.post("/api/v1/webhooks/github", json=_payload())
    assert response.status_code == 422


def test_github_webhook_rejects_non_push_events() -> None:
    response = client.post(
        "/api/v1/webhooks/github",
        headers={"X-GitHub-Event": "issues"},
        json=_payload(),
    )
    assert response.status_code == 400


def test_github_webhook_rejects_invalid_commit_sha() -> None:
    response = client.post(
        "/api/v1/webhooks/github",
        headers={"X-GitHub-Event": "push"},
        json=_payload(before="not-a-sha"),
    )
    assert response.status_code == 422


def test_github_webhook_rejects_initial_branch_push_without_before_commit() -> None:
    response = client.post(
        "/api/v1/webhooks/github",
        headers={"X-GitHub-Event": "push"},
        json=_payload(before="0" * 40),
    )
    assert response.status_code == 422
