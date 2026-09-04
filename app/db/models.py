from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class KnowledgeItemRecord(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    layer: Mapped[str] = mapped_column(String(16), index=True)
    module: Mapped[str] = mapped_column(String(128), index=True)
    feature: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), index=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class KnowledgeRelationRecord(Base):
    __tablename__ = "knowledge_relations"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "relation", name="uq_knowledge_relation"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(255), index=True)
    target_id: Mapped[str] = mapped_column(String(255), index=True)
    relation: Mapped[str] = mapped_column(String(64), index=True)


class SourceBindingRecord(Base):
    __tablename__ = "source_bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    knowledge_id: Mapped[str] = mapped_column(String(255), index=True)
    repo: Mapped[str] = mapped_column(String(255), index=True)
    ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commit: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    file: Mapped[str] = mapped_column(String(1024), index=True)
    symbol: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
