from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx

from app.knowledge.impact import analyze_impact
from app.knowledge.models import KnowledgeLayer


@dataclass(frozen=True)
class GitHubChangedFile:
    path: str
    status: str
    previous_path: str | None = None


class GitHubSourceClient:
    """Minimal GitHub source reader for Phase 3 change intake."""

    def __init__(
        self,
        *,
        token: str | None = None,
        api_url: str = "https://api.github.com",
    ) -> None:
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=api_url.rstrip("/"),
            headers=headers,
            timeout=20.0,
        )

    async def compare_files(
        self,
        repository: str,
        before: str,
        after: str,
    ) -> list[GitHubChangedFile]:
        response = await self._client.get(
            f"/repos/{repository}/compare/{before}...{after}"
        )
        response.raise_for_status()
        payload = response.json()
        return [
            GitHubChangedFile(
                path=item["filename"],
                status=item["status"],
                previous_path=item.get("previous_filename"),
            )
            for item in payload.get("files", [])
        ]

    async def fetch_text(
        self,
        repository: str,
        ref: str,
        path: str,
    ) -> str | None:
        encoded_path = quote(path, safe="/")
        response = await self._client.get(
            f"/repos/{repository}/contents/{encoded_path}",
            params={"ref": ref},
            headers={"Accept": "application/vnd.github.raw+json"},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.text

    async def close(self) -> None:
        await self._client.aclose()


def bound_source_files(catalog, repository: str, commit: str) -> set[str]:
    """Files with current L1 facts bound to repository@commit."""
    files: set[str] = set()
    for item in catalog._items.values():
        if item.layer != KnowledgeLayer.L1_ENGINEERING_FACT:
            continue
        for source in item.sources:
            if source.repo == repository and source.commit == commit:
                files.add(source.file)
    return files


async def analyze_repository_change(
    catalog,
    *,
    repository: str,
    before: str,
    after: str,
    client: GitHubSourceClient,
) -> dict[str, object]:
    """Read a GitHub compare range and produce a read-only knowledge impact report.

    Canonical Markdown knowledge is deliberately not rewritten in the webhook
    request. Regeneration/review/publish is the next Phase 3 boundary.
    """
    tracked = bound_source_files(catalog, repository, before)
    if not tracked:
        return {
            "repository": repository,
            "before": before,
            "after": after,
            "tracked_files": [],
            "files": [],
            "bound_l1": [],
            "affected": [],
            "transitions": [],
        }

    changed = await client.compare_files(repository, before, after)
    file_reports: list[dict[str, object]] = []
    bound_ids: set[str] = set()
    affected_ids: set[str] = set()
    transitions: dict[str, dict[str, str]] = {}

    for changed_file in changed:
        old_path = changed_file.previous_path or changed_file.path
        binding_path = old_path if old_path in tracked else changed_file.path
        if binding_path not in tracked:
            continue
        if not binding_path.endswith(".go"):
            continue

        old_source = ""
        new_source = ""
        if changed_file.status != "added":
            old_source = await client.fetch_text(repository, before, old_path) or ""
            if not old_source:
                raise ValueError(
                    f"cannot read old source {repository}@{before}:{old_path}"
                )
        if changed_file.status != "removed":
            new_source = await client.fetch_text(
                repository, after, changed_file.path
            ) or ""
            if not new_source:
                raise ValueError(
                    f"cannot read new source {repository}@{after}:{changed_file.path}"
                )

        report = analyze_impact(
            catalog,
            old_source,
            new_source,
            commit=before,
            repo=repository,
            file=binding_path,
        )
        file_reports.append(
            {
                "path": changed_file.path,
                "previous_path": changed_file.previous_path,
                "status": changed_file.status,
                **report,
            }
        )
        bound_ids.update(report["bound_l1"])
        affected_ids.update(report["affected"])
        for transition in report["transitions"]:
            transitions[transition["id"]] = transition

    return {
        "repository": repository,
        "before": before,
        "after": after,
        "tracked_files": sorted(tracked),
        "files": file_reports,
        "bound_l1": sorted(bound_ids),
        "affected": sorted(affected_ids),
        "transitions": [transitions[key] for key in sorted(transitions)],
    }
