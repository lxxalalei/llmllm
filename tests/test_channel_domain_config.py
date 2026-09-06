from pathlib import Path

from app.knowledge.batch_compiler import BatchKnowledgeScope
from app.knowledge.domain import KnowledgeDomainManifest


def test_mattermost_channel_domain_contains_all_business_scopes() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = KnowledgeDomainManifest.from_file(
        root / "config/knowledge_domains/mattermost-channel.json"
    )

    scopes = [
        BatchKnowledgeScope.model_validate_json((root / path).read_text(encoding="utf-8"))
        for path in manifest.scopes
    ]

    assert manifest.id == "mattermost.channel"
    assert manifest.module == "mattermost.channel"
    assert {scope.feature for scope in scopes} == {
        "channel_creation",
        "channel_membership",
        "channel_permission",
        "channel_update",
        "channel_archive_restore",
    }
    assert all(scope.module == manifest.module for scope in scopes)
    assert all(scope.pipeline == "behavior_rule" for scope in scopes)
    assert all(scope.propagation == "review" for scope in scopes)


def test_channel_scopes_use_symbols_instead_of_line_ranges() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = KnowledgeDomainManifest.from_file(
        root / "config/knowledge_domains/mattermost-channel.json"
    )

    for raw_path in manifest.scopes:
        scope = BatchKnowledgeScope.model_validate_json(
            (root / raw_path).read_text(encoding="utf-8")
        )
        assert all(not source.ranges for source in scope.sources)
        assert all(source.symbols for source in scope.sources)
