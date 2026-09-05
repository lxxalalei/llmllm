from pathlib import Path

from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus


def test_mattermost_faq_traces_back_to_code() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))

    faq = catalog.get("faq.mattermost.channel.create.limit")
    assert faq.layer == KnowledgeLayer.L4_USER_KNOWLEDGE
    assert faq.status == KnowledgeStatus.PUBLISHED

    lineage = catalog.trace_lineage(faq.id)
    assert [item.id for item in lineage] == [
        "faq.mattermost.channel.create.limit",
        "product.mattermost.channel.create.team_channel",
        "eng.mattermost.channel.create.standard_flow",
        "eng.mattermost.channel.create.type_routing",
        "eng.mattermost.channel.create.team_required",
        "eng.mattermost.channel.create.team_limit",
        "eng.mattermost.channel.create.creator_assignment",
        "eng.mattermost.channel.create.creator_membership_rule",
        "eng.mattermost.channel.create.creator_membership",
        "eng.mattermost.channel.create.join_history",
        "eng.mattermost.channel.create.default_category",
        "eng.mattermost.channel.create.join_message",
        "eng.mattermost.channel.create.websocket_event",
    ]

    sources = catalog.trace_sources(faq.id)
    assert any(
        source.repo == "mattermost/mattermost"
        and source.commit == "43b2ae87e06b06abe01f9382ec26899c54c31728"
        and source.file == "server/channels/app/channel.go"
        and source.symbol == "CreateChannelWithUser"
        for source in sources
    )
