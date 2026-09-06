from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDomainManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    module: str = Field(min_length=1)
    scopes: list[str] = Field(min_length=1)

    @classmethod
    def from_file(cls, path: str | Path) -> "KnowledgeDomainManifest":
        file_path = Path(path)
        return cls.model_validate_json(file_path.read_text(encoding="utf-8"))


def summarize_domain_previews(
    manifest: KnowledgeDomainManifest,
    previews: list[dict[str, object]],
) -> dict[str, object]:
    features: list[dict[str, object]] = []
    totals = {
        "source_files": 0,
        "symbols": 0,
        "l1": 0,
        "behavior_rules": 0,
        "l2": 0,
        "l3": 0,
        "l4": 0,
    }

    for preview in previews:
        raw_scope = preview.get("scope")
        raw_coverage = preview.get("coverage")
        if not isinstance(raw_scope, dict) or not isinstance(raw_coverage, dict):
            raise ValueError("domain preview is missing scope or coverage")
        if raw_scope.get("module") != manifest.module:
            raise ValueError(
                f"scope module {raw_scope.get('module')} does not belong to domain {manifest.module}"
            )
        feature = raw_scope.get("feature")
        if not isinstance(feature, str) or not feature:
            raise ValueError("domain preview is missing feature")

        coverage: dict[str, int] = {}
        for key in totals:
            value = raw_coverage.get(key, 0)
            if not isinstance(value, int):
                raise ValueError(f"coverage {key} must be an integer")
            coverage[key] = value
            totals[key] += value

        features.append(
            {
                "feature": feature,
                "pipeline": raw_scope.get("pipeline", "legacy"),
                "coverage": coverage,
            }
        )

    return {
        "domain": manifest.id,
        "module": manifest.module,
        "scope_count": len(previews),
        "features": features,
        "coverage": totals,
    }
