from pathlib import Path

import pytest

from app.knowledge.batch_compiler import BatchKnowledgeScope, compile_scope_preview
from app.knowledge.l1_generator import (
    EngineeringFactBatch,
    EngineeringFactDraft,
    L1Generator,
)
from app.knowledge.l2_generator import (
    EngineeringRuleBatch,
    EngineeringRuleDraft,
    L2Generator,
)


class FactExtractor:
    async def extract(self, symbols):
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key=symbol.name.lower(),
                    symbol=symbol.name,
                    title=f"Fact {symbol.name}",
                    statement=f"{symbol.name} has explicit behavior.",
                )
                for symbol in symbols
            ]
        )


class RuleExtractor:
    async def extract(self, facts, existing_rules):
        return EngineeringRuleBatch(
            rules=[
                EngineeringRuleDraft(
                    key="scope_rule",
                    title="Scope rule",
                    statement="The feature combines the compiled facts.",
                    derived_from=[item.id for item in facts],
                )
            ]
        )


@pytest.mark.asyncio
async def test_batch_compiler_combines_multiple_files_into_one_feature(tmp_path: Path) -> None:
    (tmp_path / "create.go").write_text(
        "package channel\nfunc CreateChannel() {}\n", encoding="utf-8"
    )
    (tmp_path / "member.go").write_text(
        "package channel\nfunc AddMember() {}\n", encoding="utf-8"
    )
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "ref": "main",
            "namespace": "demo.channel.membership",
            "module": "demo.channel",
            "feature": "channel_membership",
            "sources": [
                {"path": "create.go", "symbols": ["CreateChannel"]},
                {"path": "member.go", "symbols": ["AddMember"]},
            ],
        }
    )

    preview = await compile_scope_preview(
        repository_root=tmp_path,
        commit="abc123",
        scope=scope,
        l1_generator=L1Generator(FactExtractor()),
        l2_generator=L2Generator(RuleExtractor()),
    )

    assert preview["coverage"] == {
        "source_files": 2,
        "symbols": 2,
        "l1": 2,
        "l2": 1,
    }
    assert {item["id"] for item in preview["l1_items"]} == {
        "eng.demo.channel.membership.createchannel",
        "eng.demo.channel.membership.addmember",
    }
    assert preview["l2_items"][0]["derived_from"] == [
        "eng.demo.channel.membership.addmember",
        "eng.demo.channel.membership.createchannel",
    ] or set(preview["l2_items"][0]["derived_from"]) == {
        "eng.demo.channel.membership.createchannel",
        "eng.demo.channel.membership.addmember",
    }
    assert {change["change"] for change in preview["l1_changes"]} == {"added"}
    assert preview["l2_changes"] == [
        {"id": "eng.demo.channel.membership.scope_rule", "change": "added"}
    ]


@pytest.mark.asyncio
async def test_batch_compiler_rejects_missing_target_symbol(tmp_path: Path) -> None:
    (tmp_path / "channel.go").write_text(
        "package channel\nfunc CreateChannel() {}\n", encoding="utf-8"
    )
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.channel",
            "module": "demo.channel",
            "feature": "missing",
            "sources": [{"path": "channel.go", "symbols": ["NotThere"]}],
        }
    )

    with pytest.raises(ValueError, match="target symbols not found"):
        await compile_scope_preview(
            repository_root=tmp_path,
            commit="abc123",
            scope=scope,
            l1_generator=L1Generator(FactExtractor()),
            l2_generator=L2Generator(RuleExtractor()),
        )


class DuplicateFactExtractor:
    async def extract(self, symbols):
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="same_fact",
                    symbol=symbols[0].name,
                    title="Same fact",
                    statement="same",
                )
            ]
        )


@pytest.mark.asyncio
async def test_batch_compiler_rejects_cross_file_knowledge_id_collision(tmp_path: Path) -> None:
    (tmp_path / "a.go").write_text("package p\nfunc A() {}\n", encoding="utf-8")
    (tmp_path / "b.go").write_text("package p\nfunc B() {}\n", encoding="utf-8")
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.scope",
            "module": "demo",
            "feature": "scope",
            "sources": [{"path": "a.go"}, {"path": "b.go"}],
        }
    )

    with pytest.raises(ValueError, match="duplicate knowledge ids across compiled L1"):
        await compile_scope_preview(
            repository_root=tmp_path,
            commit="abc123",
            scope=scope,
            l1_generator=L1Generator(DuplicateFactExtractor()),
            l2_generator=L2Generator(RuleExtractor()),
        )
