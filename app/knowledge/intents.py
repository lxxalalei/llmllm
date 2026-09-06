from __future__ import annotations

import json
from enum import StrEnum

from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# Intent taxonomy — the routing contract of the QA assistant.
#
#   KNOWLEDGE  -> retrieval + grounded answer pipeline
#   CHAT       -> natural conversational reply (no retrieval)
#   OFF_TOPIC  -> unrelated external topic: polite redirect, no retrieval
#   SENSITIVE  -> harmful/unsafe request: refusal policy, no retrieval
#
# Extending the system = adding a taxonomy entry + its responder mode, not
# stacking keyword rules.
# ---------------------------------------------------------------------------


class Intent(StrEnum):
    KNOWLEDGE = "knowledge"
    CHAT = "chat"
    OFF_TOPIC = "off_topic"
    SENSITIVE = "sensitive"


CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": [item.value for item in Intent]},
        "reason": {"type": "string"},
    },
    "required": ["intent", "reason"],
    "additionalProperties": False,
}

CLASSIFY_INSTRUCTIONS = (
    "You route messages for an enterprise product-knowledge assistant. "
    "Classify the user message into exactly one intent:\n"
    "- knowledge: any question about the enterprise's products, code, features, "
    "rules, docs or work-related product behavior (even if our knowledge base "
    "may not cover it yet).\n"
    "- chat: greeting, thanks, farewell, asking who you are, small talk, jokes "
    "or casual workplace conversation.\n"
    "- off_topic: clearly unrelated external topics (weather, news, sports, "
    "politics, general trivia not about our products).\n"
    "- sensitive: requests for harmful, illegal, discriminatory content, or "
    "leaking confidential information.\n"
    "Return intent and a short reason."
)

_QUICK_CHAT_MARKS = (
    "你好", "您好", "哈喽", "嗨", "hello", "hi", "hey", "早上好", "中午好",
    "下午好", "晚上好", "在吗", "在么", "谢谢", "感谢", "多谢", "thanks",
    "thank you", "thx", "辛苦了", "再见", "拜拜", "bye", "晚安", "回见",
    "你是谁", "你能做什么", "你是什么", "介绍一下你", "你会什么",
    "what can you do", "who are you",
)


def quick_intent(question: str) -> Intent | None:
    """Zero-cost fast path for short, unambiguous social messages.

    Returns None when the message needs the LLM classifier (or the default
    KNOWLEDGE routing when no classifier is configured).
    """
    text = question.strip().lower()
    if not text:
        return None
    if len(text) <= 12 and any(mark in text for mark in _QUICK_CHAT_MARKS):
        return Intent.CHAT
    return None


class LLMIntentClassifier:
    """Taxonomy-based intent routing via the configured chat model."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str | None = None,
        reasoning_effort: str | None = None,
    ) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._reasoning_effort = reasoning_effort

    async def classify(self, question: str) -> Intent:
        response = await self._client.responses.create(
            model=self._model,
            instructions=CLASSIFY_INSTRUCTIONS,
            input=question,
            reasoning={"effort": self._reasoning_effort} if self._reasoning_effort else None,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "intent_classification",
                    "schema": CLASSIFY_SCHEMA,
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("intent classifier returned no structured result")
        payload = json.loads(response.output_text)
        try:
            return Intent(payload["intent"])
        except ValueError:
            return Intent.KNOWLEDGE

    async def close(self) -> None:
        await self._client.close()


async def route_intent(
    question: str,
    classifier: LLMIntentClassifier | None,
) -> Intent:
    """Full routing: fast path first, LLM taxonomy fallback, KNOWLEDGE default."""
    quick = quick_intent(question)
    if quick is not None:
        return quick
    if classifier is not None:
        try:
            return await classifier.classify(question)
        except Exception:
            return Intent.KNOWLEDGE
    return Intent.KNOWLEDGE
