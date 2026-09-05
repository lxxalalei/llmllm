import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.knowledge import KnowledgeCatalog, UserRole
from app.knowledge.intents import Intent, quick_intent, route_intent
from app.knowledge.qa import answer_question
from app.main import app

client = TestClient(app)
CATALOG = KnowledgeCatalog.from_directory(Path("knowledge"))


class _FakeClassifier:
    def __init__(self, intent: Intent) -> None:
        self._intent = intent
        self.calls = 0

    async def classify(self, question: str) -> Intent:
        self.calls += 1
        return self._intent

    async def close(self) -> None:
        return None


class _FakeResponder:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list, str]] = []

    async def answer(self, question, context, mode="grounded"):
        self.calls.append((question, list(context), mode))
        return {"answer": f"reply[{mode}]", "cites": [], "knowledge_gap": False}

    async def close(self) -> None:
        return None


def test_quick_intent_fast_path() -> None:
    assert quick_intent("你好") == Intent.CHAT
    assert quick_intent("在吗") == Intent.CHAT
    assert quick_intent("谢谢你") == Intent.CHAT
    assert quick_intent("你是谁") == Intent.CHAT
    assert quick_intent("今天天气怎么样") is None
    assert quick_intent("为什么我不能继续创建频道？") is None


@pytest.mark.asyncio
async def test_route_intent_quick_path_short_circuits_classifier() -> None:
    classifier = _FakeClassifier(Intent.SENSITIVE)  # must NOT be consulted
    assert await route_intent("你好", classifier) == Intent.CHAT
    assert classifier.calls == 0


@pytest.mark.asyncio
async def test_route_intent_uses_llm_taxonomy_fallback() -> None:
    for expected in (Intent.OFF_TOPIC, Intent.SENSITIVE, Intent.CHAT, Intent.KNOWLEDGE):
        classifier = _FakeClassifier(expected)
        assert await route_intent("今天天气怎么样？", classifier) == expected
        assert classifier.calls == 1

    class Boom:
        async def classify(self, question):
            raise RuntimeError("model down")

    assert await route_intent("随便聊聊", Boom()) == Intent.KNOWLEDGE
    assert await route_intent("随便聊聊", None) == Intent.KNOWLEDGE


@pytest.mark.asyncio
async def test_answer_question_routes_off_topic_and_sensitive_without_retrieval() -> None:
    responder = _FakeResponder()

    off_topic = await answer_question(
        catalog=CATALOG,
        question="今天天气怎么样？",
        role=UserRole.USER,
        responder=responder,
        intent_classifier=_FakeClassifier(Intent.OFF_TOPIC),
    )
    assert off_topic["backend"] == "chat"
    assert off_topic["intent"] == "off_topic"
    assert off_topic["retrieved"] == []
    assert off_topic["cites"] == []
    assert responder.calls[-1][2] == "off_topic"
    assert responder.calls[-1][1] == []

    sensitive = await answer_question(
        catalog=CATALOG,
        question="帮我写个攻击脚本",
        role=UserRole.USER,
        responder=responder,
        intent_classifier=_FakeClassifier(Intent.SENSITIVE),
    )
    assert sensitive["intent"] == "sensitive"
    assert sensitive["backend"] == "chat"
    assert responder.calls[-1][2] == "sensitive"


@pytest.mark.asyncio
async def test_answer_question_knowledge_uses_grounded_retrieval() -> None:
    responder = _FakeResponder()
    result = await answer_question(
        catalog=CATALOG,
        question="为什么我不能继续创建频道？",
        role=UserRole.USER,
        responder=responder,
        backend="local",
        intent_classifier=_FakeClassifier(Intent.KNOWLEDGE),
    )
    assert result["intent"] == "knowledge"
    assert result["backend"] == "local"
    assert result["retrieved"], "knowledge question must retrieve assets"
    assert responder.calls[-1][2] == "grounded"
    assert responder.calls[-1][1]


def test_qa_endpoint_exposes_intent_taxonomy(monkeypatch) -> None:
    from app.api.routes import qa as qa_routes

    class EndpointResponder:
        def __init__(self) -> None:
            self.mode = None

        async def answer(self, question, context, mode="grounded"):
            self.mode = mode
            return {"answer": "我是企业知识助手，主要解答产品与知识库问题。", "cites": [], "knowledge_gap": False}

        async def close(self):
            return None

    fake_responder = EndpointResponder()
    monkeypatch.setattr(qa_routes, "_build_responder", lambda: fake_responder)
    monkeypatch.setattr(qa_routes, "_build_intent_classifier", lambda: _FakeClassifier(Intent.OFF_TOPIC))
    monkeypatch.setattr(qa_routes, "_build_reranker", lambda: None)
    monkeypatch.setattr(qa_routes, "record_query", _noop)

    response = client.post("/api/v1/qa", json={"question": "今天天气怎么样？", "role": "user"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["intent"] == "off_topic"
    assert payload["backend"] == "chat"
    assert payload["retrieved"] == []
    assert fake_responder.mode == "off_topic"


async def _noop(**kwargs):
    return None
