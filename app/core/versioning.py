"""
Better Prompt — prompt version control.
Tracks prompt changes over time, diffs, and performance comparisons.
"""
from __future__ import annotations

import difflib
import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PromptVersion:
    id:        str             = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name:      str             = ""
    content:   str             = ""
    timestamp: str             = field(default_factory=lambda: datetime.utcnow().isoformat())
    parent_id: Optional[str]   = None
    tags:      list            = field(default_factory=list)
    score:     Optional[float] = None
    metadata:  dict            = field(default_factory=dict)


class VersionControl:
    """Git-like version control for prompts, backed by a JSON file."""

    def __init__(self, storage_path: str = "versions.json") -> None:
        self._path = storage_path
        self._versions: dict[str, PromptVersion] = {}
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────
    def save_version(
        self,
        name: str,
        content: str,
        tags: list = [],
        score: Optional[float] = None,
        parent_id: Optional[str] = None,
        metadata: dict = {},
    ) -> PromptVersion:
        """Save a new version of a named prompt."""
        v = PromptVersion(
            name=name,
            content=content,
            tags=list(tags),
            score=score,
            parent_id=parent_id,
            metadata=dict(metadata),
        )
        self._versions[v.id] = v
        self._persist()
        return v

    def get_diff(self, v1_id: str, v2_id: str) -> str:
        """Return a unified diff between two versions."""
        v1 = self._versions.get(v1_id)
        v2 = self._versions.get(v2_id)
        if not v1 or not v2:
            return "One or both versions not found."
        diff = "".join(
            difflib.unified_diff(
                v1.content.splitlines(keepends=True),
                v2.content.splitlines(keepends=True),
                fromfile=f"{v1.name} [{v1.id}]",
                tofile=f"{v2.name} [{v2.id}]",
            )
        )
        return diff or "No differences found."

    def get_history(self, name: str) -> list[PromptVersion]:
        """Return all versions of a named prompt, oldest first."""
        return sorted(
            [v for v in self._versions.values() if v.name == name],
            key=lambda v: v.timestamp,
        )

    def compare_performance(self, v1_id: str, v2_id: str) -> dict:
        """Compare scores between two versions."""
        v1 = self._versions.get(v1_id)
        v2 = self._versions.get(v2_id)
        if not v1 or not v2:
            return {"error": "One or both versions not found."}
        s1  = v1.score or 0.0
        s2  = v2.score or 0.0
        imp = s2 - s1
        return {
            "v1": {"id": v1.id, "name": v1.name, "score": s1},
            "v2": {"id": v2.id, "name": v2.name, "score": s2},
            "improvement":     round(imp, 4),
            "improvement_pct": round(imp / s1 * 100, 2) if s1 else 0.0,
            "better": (
                v2_id if s2 > s1 else (v1_id if s1 > s2 else "tie")
            ),
        }

    def list_names(self) -> list[str]:
        """Return a sorted list of all unique prompt names."""
        return sorted({v.name for v in self._versions.values()})

    def all_versions(self) -> list[PromptVersion]:
        """Return all versions sorted by timestamp descending."""
        return sorted(
            self._versions.values(),
            key=lambda v: v.timestamp,
            reverse=True,
        )

    # ── Private ───────────────────────────────────────────────────────────────
    def _persist(self) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(
                {k: asdict(v) for k, v in self._versions.items()},
                f,
                indent=2,
            )

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            self._versions = {
                k: PromptVersion(**v) for k, v in data.items()
            }
        except Exception:
            self._versions = {}
