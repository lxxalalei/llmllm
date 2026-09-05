from __future__ import annotations

from collections import defaultdict
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


def _ref_matches(push_ref: str, source_ref: str) -> bool:
    if push_ref == source_ref:
        return True
    if source_ref.startswith("refs/"):
        return False
    return push_ref == f"refs/heads/{source_ref}" or push_ref == f"refs/tags/{source_ref}"


def bound_source_baselines(
    catalog,
    repository: str,
    push_ref: str | None = None,
) -> dict[str, str]:
    """Current source commit for every L1-bound file in a repository/ref.

    Multiple L1 facts may point at the same file, but they must agree on the
    baseline commit. If they do not, impact analysis cannot know which source
    snapshot is authoritative and fails explicitly.
    """
    baselines: dict[str, str] = {}
    for item in catalog._items.values():
        if item.layer != KnowledgeLayer.L1_ENGINEERING_FACT:
            continue
        for source in item.sources:
            if source.repo != repository or source.commit is None:
                continue
            if (
                push_ref is not None
                and source.ref is not None
                and not _ref_matches(push_ref, source.ref)
            ):
                continue
            current = baselines.get(source.file)
            if current is not None and current != source.commit:
                raise ValueError(
                    f"multiple source commits for {repository}:{source.file}: "
                    f"{current} vs {source.commit}"
                )
            baselines[source.file] = source.commit
    return baselines


async def analyze_repository_change(
    catalog,
    *,
    repository: str,
    before: str,
    after: str,
    client: GitHubSourceClient,
    ref: str | None = None,
) -> dict[str, object]:
    """Read GitHub changes from the knowledge baseline to `after`.

    `before` is recorded from the push event, but impact analysis deliberately
    starts from each L1 SourceBinding commit. This makes a later push able to
    catch up if an earlier webhook delivery was missed. When the push provides
    a Git ref, only L1 assets bound to that ref are considered.

    Canonical Markdown knowledge is not rewritten here. Regeneration/review/
    publish is the next Phase 3 boundary.
    """
    baselines = bound_source_baselines(catalog, repository, ref)
    if not baselines:
        return {
            "repository": repository,
            "ref": ref,
            "before": before,
            "after": after,
            "tracked_files": [],
            "source_baselines": {},
            "files": [],
            "bound_l1": [],
            "affected": [],
            "transitions": [],
        }

    files_by_baseline: dict[str, set[str]] = defaultdict(set)
    for file, baseline in baselines.items():
        files_by_baseline[baseline].add(file)

    file_reports: list[dict[str, object]] = []
    bound_ids: set[str] = set()
    affected_ids: set[str] = set()
    transitions: dict[str, dict[str, str]] = {}

    for baseline, tracked_files in sorted(files_by_baseline.items()):
        changed = await client.compare_files(repository, baseline, after)
        for changed_file in changed:
            old_path = changed_file.previous_path or changed_file.path
            binding_path = old_path if old_path in tracked_files else changed_file.path
            if binding_path not in tracked_files:
                continue
            if not binding_path.endswith(".go"):
                continue

            old_source = ""
            new_source = ""
            if changed_file.status != "added":
                fetched_old = await client.fetch_text(repository, baseline, old_path)
                if fetched_old is None:
                    raise ValueError(
                        f"cannot read old source {repository}@{baseline}:{old_path}"
                    )
                old_source = fetched_old
            if changed_file.status != "removed":
                fetched_new = await client.fetch_text(
                    repository, after, changed_file.path
                )
                if fetched_new is None:
                    raise ValueError(
                        f"cannot read new source {repository}@{after}:{changed_file.path}"
                    )
                new_source = fetched_new

            report = analyze_impact(
                catalog,
                old_source,
                new_source,
                commit=baseline,
                repo=repository,
                file=binding_path,
            )
            file_reports.append(
                {
                    "path": changed_file.path,
                    "previous_path": changed_file.previous_path,
                    "status": changed_file.status,
                    "baseline": baseline,
                    "caught_up": baseline != before,
                    **report,
                }
            )
            bound_ids.update(report["bound_l1"])
            affected_ids.update(report["affected"])
            for transition in report["transitions"]:
                transitions[transition["id"]] = transition

    return {
        "repository": repository,
        "ref": ref,
        "before": before,
        "after": after,
        "tracked_files": sorted(baselines),
        "source_baselines": dict(sorted(baselines.items())),
        "files": sorted(file_reports, key=lambda item: (item["path"], item["baseline"])),
        "bound_l1": sorted(bound_ids),
        "affected": sorted(affected_ids),
        "transitions": [transitions[key] for key in sorted(transitions)],
    }
