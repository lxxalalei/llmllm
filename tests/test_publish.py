from pathlib import Path

from app.knowledge.assets import load_knowledge_file
from app.knowledge.models import (
    KnowledgeItem,
    KnowledgeLayer,
    KnowledgeStatus,
    SourceBinding,
    UserRole,
)
from app.knowledge.publish import (
    apply_publish_plan,
    plan_regeneration_publish,
    render_knowledge_item,
)


def _write(path: Path, item: KnowledgeItem) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_knowledge_item(item), encoding="utf-8")


def _l1(item_id: str, *, commit: str = "c1", content: str = "fact") -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=item_id.rsplit(".", 1)[-1],
        layer=KnowledgeLayer.L1_ENGINEERING_FACT,
        module="demo.channel",
        feature="creation",
        content=content,
        status=KnowledgeStatus.DRAFT,
        sources=[
            SourceBinding(
                repo="demo/repo",
                ref="main",
                commit=commit,
                file="channel.go",
                symbol="Create",
                start_line=1,
                end_line=3,
            )
        ],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST],
    )


def _l2(item_id: str, l1_id: str, *, content: str = "rule", version: int = 1) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title=item_id.rsplit(".", 1)[-1],
        layer=KnowledgeLayer.L2_ENGINEERING_RULE,
        module="demo.channel",
        feature="creation",
        content=content,
        status=KnowledgeStatus.DRAFT,
        version=version,
        derived_from=[l1_id],
        visible_roles=[UserRole.DEVELOPER, UserRole.TEST, UserRole.PRODUCT],
    )


def _l3(item_id: str, l2_id: str) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title="Product behavior",
        layer=KnowledgeLayer.L3_PRODUCT_LOGIC,
        module="demo.channel",
        feature="creation",
        content="published product behavior",
        status=KnowledgeStatus.PUBLISHED,
        derived_from=[l2_id],
        visible_roles=[UserRole.USER, UserRole.PRODUCT, UserRole.TEST, UserRole.DEVELOPER],
    )


def _l4(item_id: str, l3_id: str) -> KnowledgeItem:
    return KnowledgeItem(
        id=item_id,
        title="User answer",
        layer=KnowledgeLayer.L4_USER_KNOWLEDGE,
        module="demo.channel",
        feature="creation",
        content="published user answer",
        status=KnowledgeStatus.PUBLISHED,
        derived_from=[l3_id],
        visible_roles=[UserRole.USER, UserRole.PRODUCT, UserRole.TEST, UserRole.DEVELOPER],
    )


def test_publish_plan_is_dry_run_until_applied(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    l1_id = "eng.demo.channel.create.fact"
    l2_id = "eng.demo.channel.create.rule"
    l3_id = "product.demo.channel.create.behavior"
    l4_id = "faq.demo.channel.create.answer"

    l1_path = root / "l1-engineering-facts/demo/creation/fact.md"
    l2_path = root / "l2-engineering-rules/demo/creation/rule.md"
    l3_path = root / "l3-product-logic/demo/creation/behavior.md"
    l4_path = root / "l4-user-knowledge/demo/creation/answer.md"
    _write(l1_path, _l1(l1_id))
    _write(l2_path, _l2(l2_id, l1_id))
    _write(l3_path, _l3(l3_id, l2_id))
    _write(l4_path, _l4(l4_id, l3_id))

    original_l1 = l1_path.read_text(encoding="utf-8")
    original_l3 = l3_path.read_text(encoding="utf-8")
    original_l4 = l4_path.read_text(encoding="utf-8")
    new_l1 = _l1(l1_id, commit="c2")
    new_l2 = _l2(l2_id, l1_id, content="updated rule", version=2)
    preview = {
        "l1_changes": [{"id": l1_id, "change": "unchanged"}],
        "l1_items": [new_l1.model_dump(mode="json")],
        "l2_changes": [{"id": l2_id, "change": "changed"}],
        "l2_items": [new_l2.model_dump(mode="json")],
        "l3_review": [l3_id],
    }

    plan = plan_regeneration_publish(preview, knowledge_root=root)

    assert l1_path.read_text(encoding="utf-8") == original_l1
    assert l3_path.read_text(encoding="utf-8") == original_l3
    assert l4_path.read_text(encoding="utf-8") == original_l4
    assert {write.item.id for write in plan.writes} == {l1_id, l2_id, l3_id, l4_id}
    assert set(plan.index_upsert_ids) == {l1_id, l2_id, l3_id, l4_id}

    apply_publish_plan(plan)

    published_l1 = load_knowledge_file(l1_path)
    published_l2 = load_knowledge_file(l2_path)
    published_l3 = load_knowledge_file(l3_path)
    published_l4 = load_knowledge_file(l4_path)
    assert published_l1.sources[0].commit == "c2"
    assert "updated rule" in published_l2.content
    assert published_l2.version == 2
    assert published_l3.status == KnowledgeStatus.REVIEW
    assert published_l4.status == KnowledgeStatus.OUTDATED


def test_publish_adds_and_removes_git_backed_knowledge_files(tmp_path: Path) -> None:
    root = tmp_path / "knowledge"
    old_id = "eng.demo.channel.create.old_fact"
    new_id = "eng.demo.channel.create.new_fact"
    old_path = root / "l1-engineering-facts/demo/creation/old-fact.md"
    _write(old_path, _l1(old_id))

    new_item = _l1(new_id, commit="c2", content="new fact")
    preview = {
        "l1_changes": [
            {"id": old_id, "change": "removed"},
            {"id": new_id, "change": "added"},
        ],
        "l1_items": [new_item.model_dump(mode="json")],
        "l2_changes": [],
        "l2_items": [],
        "l3_review": [],
    }

    plan = plan_regeneration_publish(preview, knowledge_root=root)
    expected_new = root / "l1-engineering-facts/demo/creation/new-fact.md"
    assert plan.deletes == (old_path,)
    assert plan.writes[0].path == expected_new
    assert plan.index_delete_ids == (old_id,)
    assert plan.index_upsert_ids == (new_id,)

    apply_publish_plan(plan)

    assert not old_path.exists()
    assert expected_new.exists()
    assert load_knowledge_file(expected_new).id == new_id
