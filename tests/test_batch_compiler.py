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
from app.knowledge.keys import normalize_knowledge_key
from app.knowledge.models import KnowledgeItem
from app.knowledge.upper_generator import (
    L3Generator,
    L4Generator,
    ProductLogicBatch,
    ProductLogicDraft,
    UserKnowledgeBatch,
    UserKnowledgeDraft,
)


class FactExtractor:
    async def extract(self, symbols):
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key=normalize_knowledge_key(symbol.name),
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


class RecordingFactExtractor(FactExtractor):
    def __init__(self) -> None:
        self.batch_sizes = []

    async def extract(self, symbols):
        self.batch_sizes.append(len(symbols))
        return await super().extract(symbols)


class ProductExtractor:
    async def extract(self, rules):
        return ProductLogicBatch(
            items=[
                ProductLogicDraft(
                    key="feature_behavior",
                    title="Feature behavior",
                    statement="The feature applies the compiled rule.",
                    derived_from=[rules[0].id],
                )
            ]
        )


class UserExtractor:
    async def extract(self, logic):
        return UserKnowledgeBatch(
            items=[
                UserKnowledgeDraft(
                    key="feature_question",
                    question="What does the feature do?",
                    answer="It applies the compiled behavior.",
                    derived_from=[logic[0].id],
                )
            ]
        )


class IncompleteProductExtractor:
    async def extract(self, rules):
        return ProductLogicBatch(
            items=[
                ProductLogicDraft(
                    key="partial",
                    title="Partial",
                    statement="Only one rule is covered.",
                    derived_from=[rules[0].id],
                )
            ]
        )


class IncompleteUserExtractor:
    async def extract(self, logic):
        return UserKnowledgeBatch(
            items=[
                UserKnowledgeDraft(
                    key="partial",
                    question="What is covered?",
                    answer="Only one behavior is covered.",
                    derived_from=[logic[0].id],
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
        "eng.demo.channel.membership.create_channel",
        "eng.demo.channel.membership.add_member",
    }
    assert preview["l2_items"][0]["derived_from"] == [
        "eng.demo.channel.membership.add_member",
        "eng.demo.channel.membership.create_channel",
    ] or set(preview["l2_items"][0]["derived_from"]) == {
        "eng.demo.channel.membership.create_channel",
        "eng.demo.channel.membership.add_member",
    }
    assert {change["change"] for change in preview["l1_changes"]} == {"added"}
    assert preview["l2_changes"] == [
        {"id": "eng.demo.channel.membership.scope_rule", "change": "added"}
    ]


@pytest.mark.asyncio
async def test_batch_compiler_chunks_l1_symbol_requests(tmp_path: Path) -> None:
    (tmp_path / "many.go").write_text(
        "package p\n" + "\n".join(f"func F{index}() {{}}" for index in range(5)) + "\n",
        encoding="utf-8",
    )
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.scope",
            "module": "demo",
            "feature": "scope",
            "sources": [
                {"path": "many.go", "symbols": [f"F{index}" for index in range(5)]}
            ],
        }
    )
    extractor = RecordingFactExtractor()

    preview = await compile_scope_preview(
        repository_root=tmp_path,
        commit="abc123",
        scope=scope,
        l1_generator=L1Generator(extractor),
        l2_generator=L2Generator(RuleExtractor()),
    )

    assert extractor.batch_sizes == [4, 1]
    assert preview["coverage"]["l1"] == 5


@pytest.mark.asyncio
async def test_batch_compiler_auto_publishes_l3_and_l4(tmp_path: Path) -> None:
    (tmp_path / "feature.go").write_text(
        "package p\nfunc Feature() {}\n", encoding="utf-8"
    )
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.feature",
            "module": "demo",
            "feature": "feature",
            "propagation": "auto_publish",
            "sources": [{"path": "feature.go", "symbols": ["Feature"]}],
        }
    )

    preview = await compile_scope_preview(
        repository_root=tmp_path,
        commit="abc123",
        scope=scope,
        l1_generator=L1Generator(FactExtractor()),
        l2_generator=L2Generator(RuleExtractor()),
        l3_generator=L3Generator(ProductExtractor()),
        l4_generator=L4Generator(UserExtractor()),
    )

    assert preview["coverage"] == {
        "source_files": 1,
        "symbols": 1,
        "l1": 1,
        "l2": 1,
        "l3": 1,
        "l4": 1,
    }
    assert preview["l3_items"][0]["status"] == "published"
    assert preview["l4_items"][0]["status"] == "published"
    assert preview["l4_items"][0]["derived_from"] == [preview["l3_items"][0]["id"]]


@pytest.mark.asyncio
async def test_l3_generator_rejects_omitted_l2_parent() -> None:
    rules = [
        KnowledgeItem(
            id=f"eng.demo.rule_{index}",
            title=f"Rule {index}",
            layer="L2",
            module="demo",
            feature="demo",
            content=f"Rule {index}.",
        )
        for index in range(2)
    ]

    with pytest.raises(ValueError, match="omitted L2 parents"):
        await L3Generator(IncompleteProductExtractor()).generate(
            namespace="demo",
            module="demo",
            feature="demo",
            l2_items=rules,
        )


@pytest.mark.asyncio
async def test_l4_generator_rejects_omitted_l3_parent() -> None:
    logic = [
        KnowledgeItem(
            id=f"product.demo.behavior_{index}",
            title=f"Behavior {index}",
            layer="L3",
            module="demo",
            feature="demo",
            content=f"Behavior {index}.",
        )
        for index in range(2)
    ]

    with pytest.raises(ValueError, match="omitted L3 parents"):
        await L4Generator(IncompleteUserExtractor()).generate(
            namespace="demo",
            module="demo",
            feature="demo",
            l3_items=logic,
        )


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
                    key=f"{normalize_knowledge_key(symbols[0].name)}_same_fact",
                    symbol=symbols[0].name,
                    title="Same fact",
                    statement="same",
                )
            ]
        )


class ExcessiveFactExtractor:
    async def extract(self, symbols):
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key=f"fact_{index}",
                    symbol=symbols[0].name,
                    title=f"Fact {index}",
                    statement=f"Fact {index} is explicit.",
                )
                for index in range(16)
            ]
        )


class MissingFactExtractor:
    async def extract(self, symbols):
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="only_first",
                    symbol=symbols[0].name,
                    title="Only first",
                    statement="Only the first symbol is represented.",
                )
            ]
        )


@pytest.mark.asyncio
async def test_batch_compiler_rejects_cross_file_knowledge_id_collision(tmp_path: Path) -> None:
    (tmp_path / "a.go").write_text("package p\nfunc A() {}\n", encoding="utf-8")
    (tmp_path / "b.go").write_text("package p\nfunc A() {}\n", encoding="utf-8")
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


@pytest.mark.asyncio
async def test_batch_compiler_rejects_excessive_facts_for_one_symbol(
    tmp_path: Path,
) -> None:
    (tmp_path / "a.go").write_text("package p\nfunc A() {}\n", encoding="utf-8")
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.scope",
            "module": "demo",
            "feature": "scope",
            "sources": [{"path": "a.go", "symbols": ["A"]}],
        }
    )

    with pytest.raises(ValueError, match="more than 15 facts per symbol: A=16"):
        await compile_scope_preview(
            repository_root=tmp_path,
            commit="abc123",
            scope=scope,
            l1_generator=L1Generator(ExcessiveFactExtractor()),
            l2_generator=L2Generator(RuleExtractor()),
        )


@pytest.mark.asyncio
async def test_batch_compiler_requires_a_fact_for_each_selected_symbol(
    tmp_path: Path,
) -> None:
    (tmp_path / "a.go").write_text(
        "package p\nfunc A() {}\nfunc B() {}\n", encoding="utf-8"
    )
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.scope",
            "module": "demo",
            "feature": "scope",
            "sources": [{"path": "a.go", "symbols": ["A", "B"]}],
        }
    )

    with pytest.raises(ValueError, match="no facts for selected symbols: B"):
        await compile_scope_preview(
            repository_root=tmp_path,
            commit="abc123",
            scope=scope,
            l1_generator=L1Generator(MissingFactExtractor()),
            l2_generator=L2Generator(RuleExtractor()),
        )


@pytest.mark.asyncio
async def test_batch_compiler_supports_bounded_ranges_inside_real_symbols(
    tmp_path: Path,
) -> None:
    (tmp_path / "routes.go").write_text(
        "package p\nfunc InitRoutes() {\n  register(secured(handler))\n  register(other)\n}\n",
        encoding="utf-8",
    )
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.routes",
            "module": "demo",
            "feature": "routes",
            "sources": [
                {
                    "path": "routes.go",
                    "ranges": [
                        {"symbol": "InitRoutes", "start_line": 3, "end_line": 3}
                    ],
                }
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

    assert preview["coverage"]["symbols"] == 1
    assert preview["files"][0]["ranges"] == [
        {"symbol": "InitRoutes", "start_line": 3, "end_line": 3}
    ]
    source = preview["l1_items"][0]["sources"][0]
    assert source["symbol"] == "InitRoutes"
    assert source["start_line"] == 3
    assert source["end_line"] == 3


@pytest.mark.asyncio
async def test_batch_compiler_extracts_ranges_in_separate_requests(tmp_path: Path) -> None:
    (tmp_path / "routes.go").write_text(
        "package p\nfunc Handler() {}\nfunc InitRoutes() {\n  register(handler)\n}\n",
        encoding="utf-8",
    )
    scope = BatchKnowledgeScope.model_validate(
        {
            "repo": "demo/repo",
            "namespace": "demo.routes",
            "module": "demo",
            "feature": "routes",
            "sources": [
                {
                    "path": "routes.go",
                    "symbols": ["Handler"],
                    "ranges": [
                        {"symbol": "InitRoutes", "start_line": 4, "end_line": 4}
                    ],
                }
            ],
        }
    )
    extractor = RecordingFactExtractor()

    await compile_scope_preview(
        repository_root=tmp_path,
        commit="abc123",
        scope=scope,
        l1_generator=L1Generator(extractor),
        l2_generator=L2Generator(RuleExtractor()),
    )

    assert extractor.batch_sizes == [1, 1]


def test_batch_scope_rejects_reversed_source_range() -> None:
    with pytest.raises(ValueError, match="end_line must be greater"):
        BatchKnowledgeScope.model_validate(
            {
                "repo": "demo/repo",
                "namespace": "demo.routes",
                "module": "demo",
                "feature": "routes",
                "sources": [
                    {
                        "path": "routes.go",
                        "ranges": [
                            {"symbol": "InitRoutes", "start_line": 4, "end_line": 3}
                        ],
                    }
                ],
            }
        )
