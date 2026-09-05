from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_github_webhook_rejects_non_push_events() -> None:
    response = client.post(
        "/api/v1/webhooks/github",
        headers={"X-GitHub-Event": "issues"},
        json={
            "before": "1" * 40,
            "after": "2" * 40,
            "repository": {"full_name": "mattermost/mattermost"},
        },
    )
    assert response.status_code == 400


def test_github_webhook_rejects_initial_branch_push_without_before_commit() -> None:
    response = client.post(
        "/api/v1/webhooks/github",
        headers={"X-GitHub-Event": "push"},
        json={
            "before": "0" * 40,
            "after": "2" * 40,
            "repository": {"full_name": "mattermost/mattermost"},
        },
    )
    assert response.status_code == 422
