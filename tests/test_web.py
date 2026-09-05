from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_index_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "知识问答助手" in response.text
    assert "/api/v1/qa" in response.text
