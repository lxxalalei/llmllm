import pytest
from fastapi.testclient import TestClient

from app.knowledge.analytics import summarize
from app.main import app

client = TestClient(app)


class _FakeReranker:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[str]]] = []

    async def rerank(self, question, hits):
        self.calls.append((question, [hit.item.id for hit in hits]))
        # deterministic reorder: reverse
        return list(reversed(hits))

    async def close(self) -> None:
        return None


class _FakeResponder:
    def __init__(self, result: dict) -> None:
        self._result = result

    async def answer(self, question, context):
        return self._result

    async def close(self) -> None:
        return None


def test_qa_uses_reranker_over_wider_candidates(monkeypatch) -> None:
    from app.api.routes import qa as qa_routes

    fake_rerank = _FakeReranker()
    monkeypatch.setattr(qa_routes, "_build_reranker", lambda: fake_rerank)
    monkeypatch.setattr(
        qa_routes,
        "_build_responder",
        lambda: _FakeResponder({"answer": "ok", "cites": [], "knowledge_gap": False}),
    )
    monkeypatch.setattr(qa_routes, "record_query", _noop_record)
    response = client.post("/api/v1/qa", json={"question": "为什么我不能继续创建频道？", "role": "user", "top_k": 4})
    assert response.status_code == 200
    payload = response.json()
    assert payload["reranked"] is True
    assert len(payload["retrieved"]) <= 4
    # reranker saw wider candidate set (>= 5) than final top_k
    assert fake_rerank.calls
    assert len(fake_rerank.calls[0][1]) >= 5


def test_qa_rerank_disabled(monkeypatch) -> None:
    from app.api.routes import qa as qa_routes

    monkeypatch.setattr(qa_routes.settings, "rerank", False)
    monkeypatch.setattr(
        qa_routes,
        "_build_responder",
        lambda: _FakeResponder({"answer": "ok", "cites": [], "knowledge_gap": False}),
    )
    monkeypatch.setattr(qa_routes, "record_query", _noop_record)
    response = client.post("/api/v1/qa", json={"question": "为什么我不能继续创建频道？", "role": "user"})
    assert response.status_code == 200
    assert response.json()["reranked"] is False


def test_summarize_aggregates_gaps_backends_and_top_retrieved() -> None:
    rows = [
        {"gap": False, "backend": "hybrid", "retrieved": ["a", "b"], "question": "q1", "role": "user", "created_at": "t1"},
        {"gap": True, "backend": "hybrid", "retrieved": ["b", "c"], "question": "q2", "role": "user", "created_at": "t2"},
        {"gap": True, "backend": "local", "retrieved": ["a"], "question": "q3", "role": "product", "created_at": "t3"},
    ]
    summary = summarize(rows)
    assert summary["total"] == 3
    assert summary["gap_count"] == 2
    assert summary["gap_rate"] == round(2 / 3, 3)
    assert summary["backend_counts"] == {"hybrid": 2, "local": 1}
    assert summary["top_retrieved"][0]["knowledge_id"] == "a"
    assert len(summary["recent_gaps"]) == 2


async def _noop_record(**kwargs):
    return None


def test_analytics_endpoint_reports_store_failure(monkeypatch) -> None:
    from app.api.routes import analytics as analytics_routes

    async def _boom(**kwargs):
        raise RuntimeError("pg down")

    monkeypatch.setattr(analytics_routes, "list_queries", _boom)
    response = client.get("/api/v1/analytics/queries")
    assert response.status_code == 503


def test_analytics_endpoint_returns_queries_and_summary(monkeypatch) -> None:
    from app.api.routes import analytics as analytics_routes

    async def _fake_list(**kwargs):
        assert kwargs["gap_only"] is False
        return [
            {"gap": False, "backend": "hybrid", "retrieved": ["faq.a"], "question": "q1",
             "role": "user", "created_at": "t1", "cites": ["faq.a"], "latency_ms": 5,
             "id": 1, "reranked": True}
        ]

    monkeypatch.setattr(analytics_routes, "list_queries", _fake_list)
    response = client.get("/api/v1/analytics/queries?limit=10")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["queries"]) == 1
    assert payload["summary"]["total"] == 1
