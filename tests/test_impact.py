from pathlib import Path

from app.knowledge import KnowledgeCatalog, KnowledgeLayer, KnowledgeStatus, UserRole
from app.knowledge.impact import (
    analyze_impact,
    apply_transitions,
    bound_l1_items,
    changed_symbols,
    propose_state,
    upstream_items,
)
from app.knowledge.models import KnowledgeItem, SourceBinding

OLD_GO = """package p

func CreateChannel() int {
\treturn 1
}

func Other() int {
\treturn 2
}
"""

NEW_GO = """package p

func CreateChannel() int {
\treturn 3
}

func Other() int {
\treturn 2
}
"""


def _l1(item_id: str, symbol: str, status: KnowledgeStatus = KnowledgeStatus.DRAFT) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=item_id,
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="m",
        content="fact",
        status=status,
        sources=[SourceBinding(repo="r", commit="c1", file="f.go", symbol=symbol)],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )


def _item(item_id: str, layer: KnowledgeLayer, derived_from: list[str],
          status: KnowledgeStatus = KnowledgeStatus.DRAFT) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=item_id,
        layer=layer,
        module="m",
        content="body",
        status=status,
        derived_from=derived_from,
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )


def test_changed_symbols_detects_modified_function_only() -> None:
    changes = changed_symbols(OLD_GO, NEW_GO)
    assert [(c.name, c.change) for c in changes] == [("CreateChannel", "modified")]


def test_bound_l1_matches_symbol_and_commit() -> None:
    catalog = KnowledgeCatalog([_l1("a", "CreateChannel"), _l1("b", "CreateChannel", status=KnowledgeStatus.REVIEW)])
    bound = bound_l1_items(catalog, "CreateChannel", commit="c1")
    assert [item.id for item in bound] == ["a", "b"]
    assert bound_l1_items(catalog, "Other") == []


def test_impact_analyze_locates_l1_and_upstream_closure() -> None:
    catalog = KnowledgeCatalog(
        [
            _l1("l1.a", "CreateChannel"),
            _l1("l1.b", "Other"),
            _item("l2.a", KnowledgeLayer.L2_ENGINEERING_RULE, ["l1.a"]),
            _item("l2.b", KnowledgeLayer.L2_ENGINEERING_RULE, ["l1.b"]),
            _item("l3.a", KnowledgeLayer.L3_PRODUCT_LOGIC, ["l2.a"], status=KnowledgeStatus.PUBLISHED),
            _item("l4.a", KnowledgeLayer.L4_USER_KNOWLEDGE, ["l3.a"], status=KnowledgeStatus.PUBLISHED),
        ]
    )
    report = analyze_impact(catalog, OLD_GO, NEW_GO, commit="c1")
    assert [c["name"] for c in report["symbol_changes"]] == ["CreateChannel"]
    assert report["bound_l1"] == ["l1.a"]
    assert set(report["affected"]) == {"l1.a", "l2.a", "l3.a", "l4.a"}
    transitions = {t["id"]: t for t in report["transitions"]}
    assert transitions["l1.a"]["proposed"] == "outdated"
    assert transitions["l2.a"]["proposed"] == "outdated"
    assert transitions["l3.a"] == {"id": "l3.a", "layer": "L3", "current": "published", "proposed": "review"}
    assert transitions["l4.a"]["proposed"] == "outdated"


def test_propose_state_rules_on_real_catalog() -> None:
    catalog = KnowledgeCatalog.from_directory(Path("knowledge"))
    assert propose_state(catalog.get("eng.mattermost.channel.create.team_limit")).value == "outdated"
    assert propose_state(catalog.get("eng.mattermost.channel.create.standard_flow")).value == "outdated"
    # published L3 drops to review; review L3 and draft L4 stay
    assert propose_state(catalog.get("product.mattermost.channel.create.team_channel")).value == "review"
    assert propose_state(catalog.get("product.mattermost.channel.create.managed_category")) is None
    assert propose_state(catalog.get("faq.mattermost.channel.create.limit")).value == "outdated"
    assert propose_state(catalog.get("faq.mattermost.channel.create.space_unavailable")) is None


def test_apply_transitions_rewrites_frontmatter_on_copy(tmp_path) -> None:
    root = tmp_path / "knowledge"
    (root / "l3").mkdir(parents=True)
    p3 = root / "l3" / "logic.md"
    p3.write_text(
        "---\nid: product.demo\nlayer: L3\nmodule: m\nstatus: published\nversion: 1\n---\n\n# T\n\nbody\n",
        encoding="utf-8",
    )
    p4 = root / "faq.md"
    p4.write_text(
        "---\nid: faq.demo\nlayer: L4\nmodule: m\nstatus: published\nversion: 1\n---\n\n# Q\n\nbody\n",
        encoding="utf-8",
    )
    changed = apply_transitions(
        root,
        [
            {"id": "product.demo", "current": "published", "proposed": "review"},
            {"id": "faq.demo", "current": "published", "proposed": "outdated"},
        ],
    )
    assert len(changed) == 2
    assert "status: review" in p3.read_text(encoding="utf-8")
    assert "status: outdated" in p4.read_text(encoding="utf-8")
    catalog = KnowledgeCatalog.from_directory(root)
    assert catalog.get("product.demo").status.value == "review"
    assert catalog.get("faq.demo").status.value == "outdated"


def test_changed_symbols_reports_line_drift_as_shifted_only() -> None:
    old = "package p\n\nfunc A() {\n\tx()\n}\n\nfunc B() {\n\ty()\n}\n"
    new = "package p\n\nfunc A() {\n\tx()\n}\n\n// inserted comment\nfunc B() {\n\ty()\n}\n"
    changes = changed_symbols(old, new)
    assert [(c.name, c.change) for c in changes] == [("B", "shifted")]
