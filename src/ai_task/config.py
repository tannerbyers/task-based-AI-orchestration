from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(path)).resolve()


@dataclass(frozen=True)
class AppPaths:
    cache_root: Path
    workspace_root: Path

    @property
    def repo_cache_root(self) -> Path:
        return self.cache_root / "repos"


def get_paths() -> AppPaths:
    cache_root = _expand(os.getenv("AI_TASK_CACHE_DIR", "~/.cache/ai-task"))
    workspace_root = _expand(os.getenv("AI_TASK_WORKSPACE_DIR", "~/.local/share/ai-task/workspaces"))
    cache_root.mkdir(parents=True, exist_ok=True)
    workspace_root.mkdir(parents=True, exist_ok=True)
    (cache_root / "repos").mkdir(parents=True, exist_ok=True)
    return AppPaths(cache_root=cache_root, workspace_root=workspace_root)
