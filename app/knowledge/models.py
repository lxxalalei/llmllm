from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class KnowledgeLayer(StrEnum):
    L1_ENGINEERING_FACT = "L1"
    L2_ENGINEERING_RULE = "L2"
    L3_PRODUCT_LOGIC = "L3"
    L4_USER_KNOWLEDGE = "L4"


class KnowledgeStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    PUBLISHED = "published"
    OUTDATED = "outdated"
    DEPRECATED = "deprecated"


class UserRole(StrEnum):
    USER = "user"
    PRODUCT = "product"
    TEST = "test"
    DEVELOPER = "developer"
    ADMIN = "admin"


class RelationType(StrEnum):
    DERIVED_FROM = "derived_from"
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    AFFECTS = "affects"
    BELONGS_TO = "belongs_to"


class SourceBinding(BaseModel):
    repo: str
    ref: str | None = None
    commit: str | None = None
    file: str
    symbol: str | None = None
    start_line: int | None = None
    end_line: int | None = None


class KnowledgeItem(BaseModel):
    id: str = Field(description="Stable knowledge identifier.")
    title: str
    layer: KnowledgeLayer
    module: str
    feature: str | None = None
    content: str
    status: KnowledgeStatus = KnowledgeStatus.DRAFT
    version: int = 1
    derived_from: list[str] = Field(default_factory=list)
    behavior_rule_id: str | None = None
    sources: list[SourceBinding] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    visible_roles: list[UserRole] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KnowledgeRelation(BaseModel):
    source_id: str
    target_id: str
    relation: RelationType
