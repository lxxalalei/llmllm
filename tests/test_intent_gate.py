from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.knowledge import KnowledgeCatalog, UserRole
from app.knowledge.qa import answer_question, detect_intent
from app.main import app

client = TestClient(app)


def test_detect_intent_routes_chat_vs_knowledge() -> None:
    assert detect_intent("你好") == "chat"
    assert detect_intent("您好，在吗") == "chat"
    assert detect_intent("谢谢") == "chat"
    assert detect_intent("你是谁？") == "chat"
    assert detect_intent("hi") == "chat"
    # knowledge questions stay on the retrieval path even when they contain chat words
    assert detect_intent("你好，为什么我不能继续创建频道？") == "knowledge"
    assert detect_intent("为什么我不能继续创建频道？") == "knowledge"


@pytest.mark.asyncio
async def test_chat_gate_skips_retrieval_and_replies_naturally() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))

    class FakeResponder:
        def __init__(self) -> None:
            self.calls = []

        async def answer(self, question, context, mode="grounded"):
            self.calls.append((question, list(context), mode))
            return {"answer": "你好！我是知识问答助手，有什么可以帮你？", "cites": [], "knowledge_gap": False}

    fake = FakeResponder()
    result = await answer_question(
        catalog=catalog, question="你好", role=UserRole.USER, responder=fake
    )
    assert result["backend"] == "chat"
    assert result["retrieved"] == []
    assert result["cites"] == []
    assert fake.calls and fake.calls[0][2] == "chat"
    assert fake.calls[0][1] == []  # no knowledge context handed to the model


def test_qa_endpoint_returns_chat_backend_for_greeting(monkeypatch) -> None:
    from app.api.routes import qa as qa_routes

    class FakeResponder:
        def __init__(self) -> None:
            self.mode = None

        async def answer(self, question, context, mode="grounded"):
            self.mode = mode
            return {"answer": "你好！很高兴见到你。", "cites": [], "knowledge_gap": False}

        async def close(self) -> None:
            return None

    fake = FakeResponder()
    monkeypatch.setattr(qa_routes, "_build_responder", lambda: fake)
    monkeypatch.setattr(qa_routes, "record_query", _noop)
    response = client.post("/api/v1/qa", json={"question": "你好", "role": "user"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["backend"] == "chat"
    assert payload["retrieved"] == []
    assert payload["cites"] == []
    assert fake.mode == "chat"


async def _noop(**kwargs):
    return None
