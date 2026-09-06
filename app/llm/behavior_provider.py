from __future__ import annotations

from openai import AsyncOpenAI

from app.knowledge.behavior_rules import BehaviorRuleBatch
from app.knowledge.models import KnowledgeItem
from app.llm.openai_provider import _parse_structured, _statement


class OpenAIBehaviorRuleExtractor:
    """Extract structured behavior rules from source-backed L1 facts."""

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

    async def extract(self, facts: list[KnowledgeItem]) -> BehaviorRuleBatch:
        if not facts:
            return BehaviorRuleBatch(rules=[])

        fact_blocks = [
            f"ID: {item.id}\nTITLE: {item.title}\nFACT: {_statement(item)}"
            for item in facts
        ]
        response = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort}
            if self._reasoning_effort
            else None,
            instructions=(
                "Convert the supplied L1 engineering facts into structured BehaviorRule candidates. "
                "The L1 facts are the only semantic evidence. Do not invent product intent, actors, "
                "conditions, exceptions, ordering, state changes, or side effects that are not directly "
                "entailed by cited facts. Every rule must cite one or more supplied L1 IDs in "
                "source_fact_ids. Use conditions.all for predicates that must all hold and conditions.any "
                "only when the facts establish an OR relationship. Preserve boolean polarity exactly: "
                "blocked is not allowed, false is not true, self is not other, and examples of rejected "
                "types are not an exhaustive set unless the facts say so. Use decision for an explicit "
                "allow/reject/result when one exists. Use state_changes only for persisted or identity/state "
                "changes, and side_effects for notifications, events, history/audit, plugin lifecycle, or "
                "other observable consequences. Keep separate business behaviors as separate rules; merge "
                "only facts that describe the same behavior. Keys must be lowercase snake_case. Return "
                "structured data only."
            ),
            input="AUTHORITATIVE L1 FACTS:\n\n" + "\n\n".join(fact_blocks),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "behavior_rule_batch",
                    "schema": BehaviorRuleBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("OpenAI returned no structured behavior rules")
        return await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=response.output_text,
            model_type=BehaviorRuleBatch,
            schema_name="repaired_behavior_rule_batch",
        )

    async def close(self) -> None:
        await self._client.close()
