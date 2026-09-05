import asyncio

from app.code_index import Symbol
from app.knowledge.l1_generator import EngineeringFactBatch, EngineeringFactDraft, L1Generator
from app.knowledge.models import KnowledgeLayer, KnowledgeStatus


class FakeExtractor:
    async def extract(self, symbols: list[Symbol]) -> EngineeringFactBatch:
        return EngineeringFactBatch(
            facts=[
                EngineeringFactDraft(
                    key="team_required",
                    symbol="CreateChannelWithUser",
                    title="创建团队频道必须提供 TeamId",
                    statement="TeamId 为空时创建被拒绝。",
                )
            ]
        )


def test_l1_generator_attaches_authoritative_source_binding() -> None:
    generator = L1Generator(FakeExtractor())
    items = asyncio.run(
        generator.generate(
            namespace="mattermost.channel.create",
            module="mattermost.channel",
            feature="channel_creation",
            repo="mattermost/mattermost",
            ref="master",
            commit="43b2ae87e06b06abe01f9382ec26899c54c31728",
            file="server/channels/app/channel.go",
            symbols=[
                Symbol(
                    kind="method_declaration",
                    name="CreateChannelWithUser",
                    start_line=1,
                    end_line=20,
                    source="func (a *App) CreateChannelWithUser() {}",
                )
            ],
        )
    )

    assert len(items) == 1
    item = items[0]
    assert item.id == "eng.mattermost.channel.create.team_required"
    assert item.layer == KnowledgeLayer.L1_ENGINEERING_FACT
    assert item.status == KnowledgeStatus.DRAFT
    assert item.sources[0].repo == "mattermost/mattermost"
    assert item.sources[0].symbol == "CreateChannelWithUser"
    assert item.sources[0].start_line == 1


def test_l1_generator_rejects_unknown_model_symbol() -> None:
    class BadExtractor:
        async def extract(self, symbols: list[Symbol]) -> EngineeringFactBatch:
            return EngineeringFactBatch(
                facts=[
                    EngineeringFactDraft(
                        key="invented",
                        symbol="NotInSource",
                        title="错误来源",
                        statement="不应被接受。",
                    )
                ]
            )

    generator = L1Generator(BadExtractor())
    try:
        asyncio.run(
            generator.generate(
                namespace="mattermost.channel.create",
                module="mattermost.channel",
                feature="channel_creation",
                repo="mattermost/mattermost",
                ref="master",
                commit="abc",
                file="channel.go",
                symbols=[Symbol(kind="method_declaration", name="CreateChannel", start_line=1, end_line=2, source="func (a *App) CreateChannel() {}")],
            )
        )
    except ValueError as exc:
        assert "unknown source symbol" in str(exc)
    else:
        raise AssertionError("unknown model symbol must fail")
