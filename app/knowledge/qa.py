from __future__ import annotations

import json
from typing import Protocol

from openai import AsyncOpenAI

from app.knowledge.intents import Intent, quick_intent, route_intent
from app.knowledge.retrieval import RetrievalHit

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "cites": {"type": "array", "items": {"type": "string"}},
        "knowledge_gap": {"type": "boolean"},
    },
    "required": ["answer", "cites", "knowledge_gap"],
    "additionalProperties": False,
}

SYSTEM_INSTRUCTIONS = (
    "You are the enterprise product knowledge assistant. Answer ONLY from the "
    "supplied knowledge assets. Ground every claim in at least one supplied asset "
    "and cite its knowledge id in cites. If no supplied asset covers the question, "
    "set knowledge_gap to true and do not invent content. Match the language of "
    "the user question."
)

CHAT_INSTRUCTIONS = (
    "You are a friendly enterprise knowledge assistant. The user is chatting "
    "with you (greeting, thanks, small talk, jokes, or asking what you can do), "
    "not asking a knowledge question. Reply naturally and briefly; do not search "
    "or cite knowledge assets. If the user drifts to non-work topics, politely "
    "guide them back to product/knowledge questions. Return cites as an empty "
    "array and knowledge_gap false."
)

OFF_TOPIC_INSTRUCTIONS = (
    "You are an enterprise product-knowledge assistant. The user asked about an "
    "external topic unrelated to the enterprise's products or knowledge base "
    "(weather, news, sports, politics, general trivia, etc.). Politely explain "
    "that you focus on internal product and knowledge questions, and invite a "
    "work-related question. Do not invent external facts. Return cites as an "
    "empty array and knowledge_gap false."
)

SENSITIVE_INSTRUCTIONS = (
    "You are an enterprise product-knowledge assistant. The user request is "
    "harmful, illegal, discriminatory, or asks to leak confidential information. "
    "Briefly and politely refuse to help with it and state that you only support "
    "safe, work-related questions. Do not comply. Return cites as an empty array "
    "and knowledge_gap false."
)

NO_KNOWLEDGE_INSTRUCTIONS = (
    "You are the enterprise product knowledge assistant. The user asked a "
    "product/knowledge question, but the knowledge base has no covering asset. "
    "Politely say the knowledge base does not cover it yet. Never invent an "
    "answer. Return cites as an empty array and knowledge_gap true."
)

_MODE_INSTRUCTIONS = {
    "chat": CHAT_INSTRUCTIONS,
    "off_topic": OFF_TOPIC_INSTRUCTIONS,
    "sensitive": SENSITIVE_INSTRUCTIONS,
    "no_knowledge": NO_KNOWLEDGE_INSTRUCTIONS,
}


def detect_intent(question: str) -> str:
    """Compatibility shim for the original fast-path two-way gate."""
    return "chat" if quick_intent(question) == Intent.CHAT else "knowledge"


class QAResponder(Protocol):
    async def answer(
        self,
        question: str,
        context: list[RetrievalHit],
        mode: str = "grounded",
    ) -> dict[str, object]:
        ...


def render_context(hits: list[RetrievalHit]) -> str:
    blocks = []
    for hit in hits:
        item = hit.item
        source_lines = []
        for source in item.sources:
            source_lines.append(
                f"repo={source.repo} commit={source.commit or '-'} file={source.file} "
                f"symbol={source.symbol or '-'} lines={source.start_line}-{source.end_line}"
            )
        binding = "\n".join(f"    source: {line}" for line in source_lines)
        blocks.append(
            f"[{item.id}] ({item.layer.value}/{item.status.value}) {item.title}\n"
            f"{item.content}\n{binding}".rstrip()
        )
    return "\n\n".join(blocks)


class OpenAIQAResponder:
    """Structured-answer responder over the same OpenAI-compatible endpoint used
    by the L1 generator (base URL from settings, not process env)."""

    def __init__(self, *, api_key: str, model: str, base_url: str | None = None) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def answer(
        self,
        question: str,
        context: list[RetrievalHit],
        mode: str = "grounded",
    ) -> dict[str, object]:
        if mode in _MODE_INSTRUCTIONS:
            instructions = _MODE_INSTRUCTIONS[mode] + (
                "\nReply in the same language as the user's message."
            )
            prompt = question
        else:
            if not context:
                return {"answer": "知识库暂无覆盖该问题的已发布内容。", "cites": [], "knowledge_gap": True}
            instructions = SYSTEM_INSTRUCTIONS
            prompt = f"USER QUESTION:\n{question}\n\nKNOWLEDGE ASSETS:\n{render_context(context)}"
        response = await self._client.responses.create(
            model=self._model,
            instructions=instructions,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "qa_answer",
                    "schema": ANSWER_SCHEMA,
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("QA model returned no structured answer")
        return json.loads(response.output_text)

    async def close(self) -> None:
        await self._client.close()


async def answer_question(
    *,
    catalog,
    question: str,
    role,
    responder: QAResponder,
    top_k: int = 4,
    backend: str = "local",
    vector_index=None,
    embedder=None,
    reranker=None,
    intent_classifier=None,
) -> dict[str, object]:
    """Intent-routed, role-filtered, grounded QA.

    KNOWLEDGE   -> retrieval (hybrid/local) + optional rerank + grounded answer
    CHAT        -> natural reply, no retrieval
    OFF_TOPIC   -> polite redirect, no retrieval
    SENSITIVE   -> refusal, no retrieval
    """
    intent = await route_intent(question, intent_classifier)

    if intent != Intent.KNOWLEDGE:
        result = await responder.answer(question, [], mode=intent.value)
        return {
            "answer": result.get("answer", ""),
            "cites": [],
            "knowledge_gap": False,
            "retrieved": [],
            "backend": "chat",
            "reranked": False,
            "intent": intent.value,
        }

    hits = None
    used_backend = "local"
    used_rerank = False
    candidate_k = top_k * 2 if reranker is not None else top_k
    if backend == "hybrid" and vector_index is not None and embedder is not None:
        try:
            from app.knowledge.retrieval import retrieve_hybrid

            hits = await retrieve_hybrid(
                catalog, question, role, vector_index, embedder, top_k=candidate_k
            )
            used_backend = "hybrid"
        except Exception:
            hits = None
    if hits is None:
        from app.knowledge.retrieval import retrieve

        hits = retrieve(catalog, question, role, top_k=candidate_k)
        used_backend = "local"
    if reranker is not None and hits:
        try:
            hits = await reranker.rerank(question, hits)
            used_rerank = True
        except Exception:
            used_rerank = False
        hits = hits[:top_k]

    retrieved = [hit.item.id for hit in hits]
    if not hits:
        result = await responder.answer(question, [], mode="no_knowledge")
    else:
        result = await responder.answer(question, hits, mode="grounded")
    known = set(retrieved)
    cites = [cite for cite in result.get("cites", []) if cite in known]
    return {
        "answer": result.get("answer", ""),
        "cites": cites,
        "knowledge_gap": bool(result.get("knowledge_gap", True)) if not hits else bool(result.get("knowledge_gap", False)),
        "retrieved": retrieved,
        "backend": used_backend,
        "reranked": used_rerank,
        "intent": "knowledge",
    }
