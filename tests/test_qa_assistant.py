from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.knowledge import KnowledgeCatalog, KnowledgeLayer, UserRole
from app.knowledge.retrieval import retrieve
from app.main import app

client = TestClient(app)


def test_retrieve_user_only_returns_published_l3_l4() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))
    hits = retrieve(catalog, "为什么我不能继续创建频道？", UserRole.USER, top_k=4)
    assert hits, "expected at least one hit"
    assert hits[0].item.id == "faq.mattermost.channel.create.limit"
    for hit in hits:
        assert UserRole.USER in hit.item.visible_roles
        assert hit.item.layer in (
            KnowledgeLayer.L3_PRODUCT_LOGIC,
            KnowledgeLayer.L4_USER_KNOWLEDGE,
        )
        assert hit.item.status.value == "published"


def test_retrieve_product_normal_serve_uses_published_product_knowledge() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))
    hits = retrieve(catalog, "团队达到频道上限后还能创建频道吗", UserRole.PRODUCT, top_k=5)
    layers = {hit.item.layer for hit in hits}
    assert KnowledgeLayer.L3_PRODUCT_LOGIC in layers
    assert KnowledgeLayer.L1_ENGINEERING_FACT not in layers
    assert all(hit.item.status.value == "published" for hit in hits)


def test_retrieve_developer_review_mode_can_surface_l1_with_code_binding() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))
    hits = retrieve(
        catalog,
        "MaxChannelsPerTeam 限制在哪里生效",
        UserRole.DEVELOPER,
        top_k=5,
        review_mode=True,
    )
    assert hits[0].item.id == "eng.mattermost.channel.create.team_limit"


def test_qa_returns_503_when_llm_not_configured(monkeypatch) -> None:
    from app.api.routes import qa as qa_routes

    monkeypatch.setattr(qa_routes.settings, "llm_provider", None)
    monkeypatch.setattr(qa_routes.settings, "llm_api_key", None)
    monkeypatch.setattr(qa_routes.settings, "llm_model", None)
    response = client.post("/api/v1/qa", json={"question": "为什么不能创建频道？", "role": "user"})
    assert response.status_code == 503


class _FakeResponder:
    def __init__(self, result: dict) -> None:
        self._result = result
        self.calls = []

    async def answer(self, question, context, mode="grounded"):
        self.calls.append((question, [hit.item.id for hit in context], mode))
        return self._result

    async def close(self) -> None:
        return None


def test_qa_endpoint_hardens_citations_and_reports_gap(monkeypatch) -> None:
    from app.api.routes import qa as qa_routes

    fake = _FakeResponder(
        {
            "answer": "因为团队频道数量达到上限。",
            "cites": ["faq.mattermost.channel.create.limit", "not.a.real.id"],
            "knowledge_gap": False,
        }
    )
    monkeypatch.setattr(qa_routes, "_build_responder", lambda: fake)
    monkeypatch.setattr(qa_routes, "_build_intent_classifier", lambda: None)
    monkeypatch.setattr(qa_routes.settings, "retrieval_backend", "local")
    response = client.post("/api/v1/qa", json={"question": "为什么我不能继续创建频道？", "role": "user"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "因为团队频道数量达到上限。"
    assert payload["knowledge_gap"] is False
    assert [cite["id"] for cite in payload["cites"]] == ["faq.mattermost.channel.create.limit"]
    assert payload["cites"][0]["status"] == "published"
    assert "faq.mattermost.channel.create.limit" in payload["retrieved"]
    assert fake.calls and fake.calls[0][0] == "为什么我不能继续创建频道？"
    assert fake.calls[0][2] == "grounded"


def test_qa_endpoint_gap_flag_passthrough(monkeypatch) -> None:
    from app.api.routes import qa as qa_routes

    fake = _FakeResponder({"answer": "暂无覆盖。", "cites": [], "knowledge_gap": True})
    monkeypatch.setattr(qa_routes, "_build_responder", lambda: fake)
    monkeypatch.setattr(qa_routes, "_build_intent_classifier", lambda: None)
    monkeypatch.setattr(qa_routes.settings, "retrieval_backend", "local")
    response = client.post("/api/v1/qa", json={"question": "这个问题知识库没有", "role": "user"})
    assert response.status_code == 200
    assert response.json()["knowledge_gap"] is True


def test_qa_rejects_invalid_role_and_short_question() -> None:
    assert client.post("/api/v1/qa", json={"question": "x", "role": "user"}).status_code == 422
    assert client.post("/api/v1/qa", json={"question": "为什么", "role": "bogus"}).status_code == 422


def test_parse_answer_text_tolerates_fences_and_prose() -> None:
    from app.knowledge.qa import _parse_answer_text

    plain = _parse_answer_text('{"answer": "a", "cites": [], "knowledge_gap": false}')
    assert plain["answer"] == "a"
    fenced = _parse_answer_text('```json\n{"answer": "b", "cites": [], "knowledge_gap": false}\n```')
    assert fenced["answer"] == "b"
    prose = _parse_answer_text('Sure! Here is the answer: {"answer": "c", "cites": [], "knowledge_gap": false} Thanks!')
    assert prose["answer"] == "c"


def test_parse_answer_text_reports_corrupt_output() -> None:
    from app.knowledge.qa import _parse_answer_text

    with pytest.raises(ValueError, match="non-JSON"):
        _parse_answer_text("oops this is not json")
