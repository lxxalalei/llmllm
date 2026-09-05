import pytest

from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.impact import changed_symbols
from app.knowledge.l1_generator import EngineeringFactBatch, EngineeringFactDraft, L1Generator
from app.knowledge.models import KnowledgeItem, SourceBinding
from app.knowledge.regeneration import regenerate_go_file_l1


def _l1(item_id: str, symbol: str | None) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=item_id,
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="demo.channel",
        feature="creation",
        content="fact",
        status=KnowledgeStatus.DRAFT,
        sources=[
            SourceBinding(
                repo="demo/repo",
                ref="main",
                commit="c1",
                file="channel.go",
                symbol=symbol,
            )
        ],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )


def test_duplicate_go_method_names_fail_until_receiver_identity_is_supported() -> None:
    source = """package p

type A struct{}
type B struct{}

func (a *A) Run() {}
func (b *B) Run() {}
"""
    with pytest.raises(ValueError, match="duplicate Go symbol name"):
        changed_symbols(source, source)


class MustNotExtract:
    async def extract(self, symbols):
        raise AssertionError("model should not run")

    async def extract_incremental(self, symbols, existing_facts):
        raise AssertionError("model should not run")


@pytest.mark.asyncio
async def test_symbol_less_l1_binding_is_not_silently_dropped() -> None:
    source = """package p

func Keep() int {
    return 2
}
"""
    catalog = KnowledgeCatalog([_l1("eng.demo.channel.create.fact", None)])
    with pytest.raises(ValueError, match="source binding has no symbol"):
        await regenerate_go_file_l1(
            catalog=catalog,
            repo="demo/repo",
            baseline="c1",
            after="c2",
            old_file="channel.go",
            new_file="channel.go",
            old_source=source,
            new_source="// shifted\n" + source,
            l1_generator=L1Generator(MustNotExtract()),
        )


class CollisionExtractor:
    async def extract(self, symbols):
        raise AssertionError("incremental path expected")

    async def extract_incremental(self, symbols, existing_facts):
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="kept",
                    symbol="Change",
                    title="Collision",
                    statement="This id collides with the carried fact.",
                )
            ]
        )


@pytest.mark.asyncio
async def test_generated_l1_id_cannot_collide_with_carried_fact() -> None:
    old_source = """package p

func Change() int {
    return 1
}

func Keep() int {
    return 2
}
"""
    new_source = """package p

func Change() int {
    return 3
}

func Keep() int {
    return 2
}
"""
    catalog = KnowledgeCatalog(
        [
            _l1("eng.demo.channel.create.changed", "Change"),
            _l1("eng.demo.channel.create.kept", "Keep"),
        ]
    )
    with pytest.raises(ValueError, match="duplicate knowledge id"):
        await regenerate_go_file_l1(
            catalog=catalog,
            repo="demo/repo",
            baseline="c1",
            after="c2",
            old_file="channel.go",
            new_file="channel.go",
            old_source=old_source,
            new_source=new_source,
            l1_generator=L1Generator(CollisionExtractor()),
        )
