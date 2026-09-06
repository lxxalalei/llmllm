from __future__ import annotations

from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.code_index import Symbol
from app.knowledge.l1_generator import EngineeringFactBatch
from app.knowledge.l2_generator import EngineeringRuleBatch
from app.knowledge.models import KnowledgeItem
from app.knowledge.upper_generator import (
    ProductLogicBatch,
    UserKnowledgeBatch,
)

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


def _statement(item: KnowledgeItem) -> str:
    lines = item.content.strip().splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
    return "\n".join(lines).strip()


def _requires_upward_rule(item: KnowledgeItem) -> bool:
    """Identify source facts whose gates must not disappear during L2 synthesis."""
    text = f"{item.title}\n{_statement(item)}".casefold()
    markers = (
        "permission",
        " reject",
        "rejects",
        " denied",
        "denies",
        " block",
        "blocked",
        "restricted",
        "requirement",
        "unless ",
        "forbidden",
    )
    return any(marker in text for marker in markers)


def _requires_standalone_rule(item: KnowledgeItem) -> bool:
    text = f"{item.title}\n{_statement(item)}".casefold()
    return "default channel" in text or "defaultchannelname" in text


def _missing_required_fact_ids(
    facts: list[KnowledgeItem], rules: EngineeringRuleBatch
) -> set[str]:
    result: set[str] = set()
    for fact in facts:
        if not _requires_upward_rule(fact):
            continue
        matching = [rule for rule in rules.rules if fact.id in rule.derived_from]
        if not matching:
            result.add(fact.id)
        elif _requires_standalone_rule(fact) and not any(
            rule.derived_from == [fact.id] for rule in matching
        ):
            result.add(fact.id)
    return result


def _strip_json_fence(value: str) -> str:
    """Accept provider-added Markdown only when it wraps the entire JSON value."""
    stripped = value.strip()
    if not stripped.startswith("```") or not stripped.endswith("```"):
        return value
    first_newline = stripped.find("\n")
    if first_newline == -1:
        return value
    opening = stripped[:first_newline].lower()
    if opening not in {"```", "```json"}:
        return value
    return stripped[first_newline + 1 : -3].strip()


async def _parse_structured(
    *,
    client: AsyncOpenAI,
    model: str,
    reasoning_effort: str | None,
    value: str,
    model_type: type[StructuredModel],
    schema_name: str,
) -> StructuredModel:
    cleaned = _strip_json_fence(value)
    for attempt in range(3):
        error_message = ""
        try:
            return model_type.model_validate_json(cleaned)
        except ValidationError as error:
            if attempt == 2:
                raise
            error_message = str(error)
        repair = await client.responses.create(
            model=model,
            reasoning={"effort": reasoning_effort} if reasoning_effort else None,
            instructions=(
                "Repair the supplied malformed JSON so it validates against the response "
                "schema. Preserve its meaning exactly. Escape control characters inside JSON "
                "strings, remove Markdown, and obey all list length constraints. When a list is "
                "too long, merge overlapping items without dropping dependency IDs. Return only "
                "the repaired structured value."
            ),
            input=f"VALIDATION ERROR:\n{error_message}\n\nVALUE TO REPAIR:\n{cleaned}",
            text={
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": model_type.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not repair.output_text:
            raise ValueError("OpenAI returned no repaired structured output")
        cleaned = _strip_json_fence(repair.output_text)
    raise AssertionError("structured repair loop terminated unexpectedly")


class OpenAIEngineeringFactExtractor:
    """Extract code facts with OpenAI Structured Outputs.

    The model only proposes semantic facts. Repo/ref/file/symbol bindings are
    validated and attached by L1Generator.
    """

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

    async def _extract(
        self,
        symbols: list[Symbol],
        existing_facts: list[KnowledgeItem] | None = None,
    ) -> EngineeringFactBatch:
        if not symbols:
            return EngineeringFactBatch(facts=[])

        source_blocks = []
        for symbol in symbols:
            source_blocks.append(
                f"SYMBOL: {symbol.name}\nLINES: {symbol.start_line}-{symbol.end_line}\n```\n{symbol.source}\n```"
            )

        existing_block = ""
        if existing_facts:
            existing_lines = []
            for item in existing_facts:
                key = item.id.rsplit(".", 1)[-1]
                symbol = item.sources[0].symbol if item.sources else None
                existing_lines.append(
                    f"KEY: {key}\nSYMBOL: {symbol or '-'}\nTITLE: {item.title}\nFACT: {_statement(item)}"
                )
            existing_block = (
                "\n\nEXISTING FACTS FROM THE PREVIOUS CODE VERSION:\n"
                + "\n\n".join(existing_lines)
            )

        instructions = (
            "You extract L1 engineering facts from source code. "
            "Return only facts explicitly supported by the supplied code. "
            "Do not infer product intent, user expectations, or undocumented behavior. "
            "Each fact must be independently useful, concise, and non-duplicative. "
            "Prefer one fact that combines related predicates, branches, and outcomes over "
            "separate atomic facts plus a summary of the same behavior. Never emit both. "
            "Typically emit 1-5 facts per symbol. HARD LIMIT: never emit more than 15 "
            "facts for one symbol, including complex orchestration. "
            "Prioritize business invariants, authorization or policy gates, persistence, "
            "data cleanup, audit/history writes, actor/requestor data flow, plugin lifecycle, "
            "and externally observable side effects. Preserve source order when describing "
            "a sequence; if order is not established, do not claim one. "
            "Combine routine parameter validation and response mechanics unless they define "
            "a materially different permission, state transition, or public contract. "
            "Do not omit an option or actor identifier when it changes downstream behavior. "
            "Return at least one fact for every supplied SYMBOL because each symbol was "
            "explicitly selected as feature evidence. Before returning, compare every pair "
            "of facts for the same symbol and remove restatements of the same behavior. "
            "Use only one of the supplied symbol names in each fact.symbol. "
            "Use a stable key matching ^[a-z0-9_]+$: ASCII lowercase letters, digits, "
            "and underscores only. Every key must begin with the fact's complete source "
            "symbol converted to snake_case, followed by a concise behavior suffix; for "
            "example AddChannelMember uses add_channel_member_existing_member, never a "
            "generic existing_member key. Never copy uppercase symbol casing into the key."
        )
        if existing_facts:
            instructions += (
                " Existing facts are from the previous code version. "
                "When the same semantic fact is still supported, reuse its exact existing KEY. "
                "Omit an existing key when that fact is no longer supported. "
                "Use a new key only for a genuinely new fact."
            )

        reasoning = (
            {"effort": self._reasoning_effort} if self._reasoning_effort else None
        )
        response = await self._client.responses.create(
            model=self._model,
            instructions=instructions,
            input="\n\n".join(source_blocks) + existing_block,
            reasoning=reasoning,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "engineering_fact_batch",
                    "schema": EngineeringFactBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("OpenAI returned no structured engineering facts")
        candidate = await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=response.output_text,
            model_type=EngineeringFactBatch,
            schema_name="repaired_engineering_fact_batch",
        )

        candidate_blocks = [
            f"KEY: {fact.key}\nSYMBOL: {fact.symbol}\nFACT: {fact.statement}"
            for fact in candidate.facts
        ]
        review = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort}
            if self._reasoning_effort
            else None,
            instructions=(
                "You are the final source-grounding verifier for candidate L1 facts. "
                "Compare every clause with the authoritative source symbols. Rewrite or "
                "remove unsupported clauses while preserving correct stable keys. Check "
                "boolean condition scope exactly: distinguish self from non-self, any from "
                "some, accepted types from examples of rejected types, and exceptions from "
                "the general rule. If code accepts only an enumerated set, state that set or "
                "its full complement; never turn two rejected examples into an exhaustive "
                "rejection set. A permission check outside a self/non-self branch applies to "
                "both. Do not infer behavior outside supplied code. Return at least one fact "
                "for every supplied SYMBOL, at most 15 per symbol, using lowercase snake_case "
                "keys prefixed by the complete snake_case source symbol and no commentary."
            ),
            input=(
                "AUTHORITATIVE SOURCE SYMBOLS:\n\n"
                + "\n\n".join(source_blocks)
                + "\n\nCANDIDATE L1 FACTS TO VERIFY:\n\n"
                + "\n\n".join(candidate_blocks)
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "verified_engineering_fact_batch",
                    "schema": EngineeringFactBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not review.output_text:
            raise ValueError("OpenAI returned no verified engineering facts")
        verified = await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=review.output_text,
            model_type=EngineeringFactBatch,
            schema_name="repaired_verified_engineering_fact_batch",
        )
        return verified

    async def extract(self, symbols: list[Symbol]) -> EngineeringFactBatch:
        return await self._extract(symbols)

    async def extract_incremental(
        self,
        symbols: list[Symbol],
        existing_facts: list[KnowledgeItem],
    ) -> EngineeringFactBatch:
        return await self._extract(symbols, existing_facts)

    async def close(self) -> None:
        """Close the underlying HTTP client (required before asyncio loop shutdown)."""
        await self._client.close()


class OpenAIEngineeringRuleExtractor:
    """Synthesize L2 engineering rules from the current L1 feature scope."""

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

    async def extract(
        self,
        facts: list[KnowledgeItem],
        existing_rules: list[KnowledgeItem],
    ) -> EngineeringRuleBatch:
        if not facts:
            return EngineeringRuleBatch(rules=[])

        fact_blocks = [
            f"ID: {item.id}\nTITLE: {item.title}\nFACT: {_statement(item)}"
            for item in facts
        ]
        existing_block = ""
        if existing_rules:
            rule_blocks = []
            for item in existing_rules:
                key = item.id.rsplit(".", 1)[-1]
                rule_blocks.append(
                    f"KEY: {key}\nTITLE: {item.title}\nRULE: {_statement(item)}\n"
                    f"DERIVED_FROM: {', '.join(item.derived_from)}"
                )
            existing_block = (
                "\n\nEXISTING L2 RULES FROM THE PREVIOUS KNOWLEDGE VERSION:\n"
                + "\n\n".join(rule_blocks)
            )

        reasoning = (
            {"effort": self._reasoning_effort} if self._reasoning_effort else None
        )
        response = await self._client.responses.create(
            model=self._model,
            instructions=(
                "You synthesize L2 engineering rules from supplied L1 engineering facts. "
                "Rules are developer-facing technical/domain rules, not product intent or user documentation. "
                "Every derived_from id must be one of the supplied L1 IDs. "
                "Each key must match ^[a-z0-9_]+$: ASCII lowercase letters, digits, "
                "and underscores only. The resulting L2 IDs share a namespace with the "
                "supplied L1 IDs, so an L2 key must not equal the final key segment of any "
                "supplied L1 ID. Name a rule-level abstraction instead of copying a fact key. "
                "Existing rules are from the previous knowledge version. "
                "If the same engineering rule remains supported, reuse its exact existing KEY. "
                "Omit rules no longer supported and add a new key only for a genuinely new rule. "
                "Return no more than 15 useful, non-duplicative rules for a feature. "
                "A rule should synthesize an invariant, ordering constraint, bypass obligation, "
                "or lifecycle consequence across facts; it should not merely paraphrase one fact. "
                "Every clause in a rule must be directly entailed by its derived_from facts. "
                "Do not invent or broaden actors, exceptions, ordering, error handling, or side "
                "effects to make a rule sound complete. Do not use absolute words such as only, "
                "all, never, or must unless the supplied facts establish that exact constraint. "
                "Merge related gates into a layered rule and related persistence/notification/plugin "
                "effects into lifecycle rules. Do not promote routine request validation, HTTP response "
                "shape or status, handler delegation, logging, or cache invalidation into a standalone "
                "L2 rule unless multiple facts establish a broader engineering constraint. "
                "When selecting the limited rule set, prioritize in this order: layered authorization "
                "and policy gates; integrity prerequisites and explicit bypass obligations; persistence "
                "and dependent-state cleanup; lifecycle side effects; actor/requestor semantics. "
                "Treat type checks, idempotence, response formatting, and isolated special cases as "
                "lower priority unless they participate in a broader invariant."
            ),
            input="CURRENT L1 FACTS:\n\n" + "\n\n".join(fact_blocks) + existing_block,
            reasoning=reasoning,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "engineering_rule_batch",
                    "schema": EngineeringRuleBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not response.output_text:
            raise ValueError("OpenAI returned no structured engineering rules")
        candidate = await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=response.output_text,
            model_type=EngineeringRuleBatch,
            schema_name="repaired_engineering_rule_batch",
        )

        candidate_blocks = [
            f"KEY: {rule.key}\nRULE: {rule.statement}\n"
            f"DERIVED_FROM: {', '.join(rule.derived_from)}"
            for rule in candidate.rules
        ]
        review = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort} if self._reasoning_effort else None,
            instructions=(
                "You are the final technical verifier for candidate L2 rules. Rewrite or remove "
                "any rule clause not directly entailed by its cited L1 facts. Preserve useful rules "
                "and their stable keys when correct. Check conditional scope, accepted/rejected type "
                "sets, actor identity, ordering, and side effects exactly. A fact applying generally "
                "must not be negated by another fact whose behavior is limited to non-space channels. "
                "Reason about filtered-set cardinality literally: if FilterNonGroupChannelMembers "
                "returns zero non-members for a single target, that target is not a non-group member; "
                "do not reverse that membership polarity. Keep distinct add and removal group gates "
                "separate when their predicates differ. A predicate named Is...Blocked returning true "
                "means the operation is blocked, not allowed; preserve that boolean polarity. Ensure "
                "every supplied authorization, eligibility, "
                "permission, explicit rejection, and user-visible restriction fact is represented by at "
                "least one rule; add a corrected rule or replace a lower-priority mechanics rule when one "
                "is missing. A default-resource restriction must be its own focused rule; do not "
                "merge it with unrelated space, group, team-integrity, or lifecycle cases. "
                "Do not infer behavior for functions or branches absent from cited facts. Every "
                "derived_from must be a supplied L1 ID. Return at most 15 corrected rules using "
                "lowercase snake_case keys, with no commentary."
            ),
            input=(
                "AUTHORITATIVE L1 FACTS:\n\n"
                + "\n\n".join(fact_blocks)
                + "\n\nCANDIDATE L2 RULES TO VERIFY:\n\n"
                + "\n\n".join(candidate_blocks)
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "verified_engineering_rule_batch",
                    "schema": EngineeringRuleBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not review.output_text:
            raise ValueError("OpenAI returned no verified engineering rules")
        verified = await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=review.output_text,
            model_type=EngineeringRuleBatch,
            schema_name="repaired_verified_engineering_rule_batch",
        )
        missing_ids = _missing_required_fact_ids(facts, verified)
        if not missing_ids:
            return verified

        verified_blocks = [
            f"KEY: {rule.key}\nRULE: {rule.statement}\n"
            f"DERIVED_FROM: {', '.join(rule.derived_from)}"
            for rule in verified.rules
        ]
        missing_blocks = [
            block
            for item, block in zip(facts, fact_blocks, strict=True)
            if item.id in missing_ids
        ]
        coverage_repair = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort}
            if self._reasoning_effort
            else None,
            instructions=(
                "Repair the L2 rule set so every REQUIRED MISSING L1 FACT is cited by at least "
                "one directly entailed rule. These facts contain authorization, permission, "
                "eligibility, or explicit rejection gates and may not be omitted. A default-resource "
                "restriction must be a standalone focused rule, never part of a mixed special-case "
                "rule. Preserve correct "
                "stable keys and existing rules where possible. Merge related rules or replace "
                "lower-priority request/response mechanics to stay within 15 rules. Preserve exact "
                "condition polarity, actor scope, type sets, exceptions, and FilterNonGroupChannelMembers "
                "empty/non-empty meaning. Every derived_from must be an authoritative L1 ID. Return "
                "only the complete corrected rule batch."
            ),
            input=(
                "AUTHORITATIVE L1 FACTS:\n\n"
                + "\n\n".join(fact_blocks)
                + "\n\nREQUIRED MISSING L1 FACTS:\n\n"
                + "\n\n".join(missing_blocks)
                + "\n\nCURRENT VERIFIED L2 RULES:\n\n"
                + "\n\n".join(verified_blocks)
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "coverage_repaired_engineering_rule_batch",
                    "schema": EngineeringRuleBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not coverage_repair.output_text:
            raise ValueError("OpenAI returned no coverage-repaired engineering rules")
        repaired = await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=coverage_repair.output_text,
            model_type=EngineeringRuleBatch,
            schema_name="repaired_coverage_engineering_rule_batch",
        )
        still_missing = _missing_required_fact_ids(facts, repaired)
        if still_missing:
            raise ValueError(
                "L2 synthesis omitted required gate facts: "
                + ", ".join(sorted(still_missing))
            )
        return repaired

    async def close(self) -> None:
        await self._client.close()


class OpenAIProductLogicExtractor:
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

    async def extract(self, rules: list[KnowledgeItem]) -> ProductLogicBatch:
        blocks = [
            f"ID: {item.id}\nTITLE: {item.title}\nRULE: {_statement(item)}"
            for item in rules
        ]
        response = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort} if self._reasoning_effort else None,
            instructions=(
                "Translate supplied L2 engineering rules into concise L3 product behavior "
                "for an open-source code-derived knowledge base. Group related rules into "
                "user-recognizable capabilities. Do not invent intent, UI, timing, guarantees, "
                "or behavior absent from the rules. Preserve conditional scope, actor identity, "
                "permission applicability, accepted/rejected type sets, and exception polarity "
                "exactly. Every derived_from must be a supplied L2 ID. Use lowercase snake_case "
                "keys. Return exactly one item per supplied L2 rule, with exactly that one L2 ID "
                "in derived_from, for 3-15 non-duplicative items."
            ),
            input="CURRENT L2 RULES:\n\n" + "\n\n".join(blocks),
            text={"format": {"type": "json_schema", "name": "product_logic_batch", "schema": ProductLogicBatch.model_json_schema(), "strict": True}},
        )
        if not response.output_text:
            raise ValueError("OpenAI returned no structured product logic")
        candidate = await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=response.output_text,
            model_type=ProductLogicBatch,
            schema_name="repaired_product_logic_batch",
        )
        candidate_blocks = [
            f"KEY: {item.key}\nBEHAVIOR: {item.statement}\n"
            f"DERIVED_FROM: {', '.join(item.derived_from)}"
            for item in candidate.items
        ]
        review = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort}
            if self._reasoning_effort
            else None,
            instructions=(
                "You are the final grounding verifier for candidate L3 product behavior. "
                "Rewrite or remove every clause not directly entailed by its cited L2 rules. "
                "Preserve correct stable keys. Check permission scope, self versus non-self, "
                "guest versus non-guest, accepted/rejected type-set completeness, group-membership "
                "polarity, Is...Blocked boolean polarity, exceptions, ordering, and side effects exactly. Do not convert examples "
                "into exhaustive sets or implementation details into new product guarantees. Every "
                "supplied L2 rule must be translated into exactly one complete item, preserving every "
                "material clause; citing a rule while omitting one of its clauses is not coverage. "
                "Every item must have exactly one derived_from containing its supplied L2 ID. Return 3-15 "
                "corrected items using lowercase "
                "snake_case keys, with no commentary."
            ),
            input=(
                "AUTHORITATIVE L2 RULES:\n\n"
                + "\n\n".join(blocks)
                + "\n\nCANDIDATE L3 BEHAVIOR TO VERIFY:\n\n"
                + "\n\n".join(candidate_blocks)
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "verified_product_logic_batch",
                    "schema": ProductLogicBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not review.output_text:
            raise ValueError("OpenAI returned no verified product logic")
        return await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=review.output_text,
            model_type=ProductLogicBatch,
            schema_name="repaired_verified_product_logic_batch",
        )

    async def close(self) -> None:
        await self._client.close()


class OpenAIUserKnowledgeExtractor:
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

    async def extract(self, logic: list[KnowledgeItem]) -> UserKnowledgeBatch:
        blocks = [
            f"ID: {item.id}\nTITLE: {item.title}\nBEHAVIOR: {_statement(item)}"
            for item in logic
        ]
        response = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort} if self._reasoning_effort else None,
            instructions=(
                "Create practical Chinese L4 FAQ entries from supplied L3 product behavior. "
                "Answers must be understandable to ordinary users and strictly grounded in L3. "
                "The question's premise is also a factual claim: its actor, permission, condition, "
                "allowed/blocked direction, and exception polarity must match L3. Cover the main "
                "why/can/how/what-happens questions without inventing UI steps. Every derived_from "
                "must be a supplied L3 ID. Use lowercase snake_case keys and return 1-3 FAQs per "
                "L3 item, at most 30 total."
            ),
            input="CURRENT L3 PRODUCT BEHAVIOR:\n\n" + "\n\n".join(blocks),
            text={"format": {"type": "json_schema", "name": "user_knowledge_batch", "schema": UserKnowledgeBatch.model_json_schema(), "strict": True}},
        )
        if not response.output_text:
            raise ValueError("OpenAI returned no structured user knowledge")
        candidate = await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=response.output_text,
            model_type=UserKnowledgeBatch,
            schema_name="repaired_user_knowledge_batch",
        )
        candidate_blocks = [
            f"KEY: {item.key}\nQUESTION: {item.question}\nANSWER: {item.answer}\n"
            f"DERIVED_FROM: {', '.join(item.derived_from)}"
            for item in candidate.items
        ]
        review = await self._client.responses.create(
            model=self._model,
            reasoning={"effort": self._reasoning_effort}
            if self._reasoning_effort
            else None,
            instructions=(
                "You are the final grounding verifier for candidate Chinese L4 FAQs. Compare "
                "both each QUESTION premise and its ANSWER with the cited authoritative L3 "
                "behavior. Rewrite or remove unsupported or misleading entries while preserving "
                "correct stable keys. Explicitly check allowed versus blocked, guest versus "
                "non-guest, self versus other user, group member versus non-member, permission "
                "scope, type-set completeness, Is...Blocked boolean meaning, and exception polarity. Never answer a reversed "
                "premise as though it were true; correct the question itself. Avoid vague wording "
                "such as '可能' when L3 states a definite outcome. Every derived_from must be a "
                "supplied L3 ID, and every supplied L3 item must have at least one FAQ. Return 1-3 "
                "FAQs per L3 item, at most 30 total, with lowercase "
                "snake_case keys and no commentary."
            ),
            input=(
                "AUTHORITATIVE L3 PRODUCT BEHAVIOR:\n\n"
                + "\n\n".join(blocks)
                + "\n\nCANDIDATE L4 FAQS TO VERIFY:\n\n"
                + "\n\n".join(candidate_blocks)
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "verified_user_knowledge_batch",
                    "schema": UserKnowledgeBatch.model_json_schema(),
                    "strict": True,
                }
            },
        )
        if not review.output_text:
            raise ValueError("OpenAI returned no verified user knowledge")
        return await _parse_structured(
            client=self._client,
            model=self._model,
            reasoning_effort=self._reasoning_effort,
            value=review.output_text,
            model_type=UserKnowledgeBatch,
            schema_name="repaired_verified_user_knowledge_batch",
        )

    async def close(self) -> None:
        await self._client.close()
