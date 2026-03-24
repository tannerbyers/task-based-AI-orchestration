from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import datetime as dt
import yaml


DEFAULT_STAGE_ARTIFACTS = {
    "investigate": "01-investigate.md",
    "plan": "02-plan.md",
    "execute": "03-execute.md",
    "review": "04-review.md",
}


@dataclass
class Scope:
    files: list[str] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)


@dataclass
class ToolPolicy:
    tier: int = 1
    allowed_tools: list[str] = field(default_factory=lambda: ["aider"])
    fallback_tools: list[str] = field(default_factory=list)
    max_files: int = 5
    max_iterations: int = 1


@dataclass
class Verification:
    commands: list[str] = field(default_factory=list)


@dataclass
class Task:
    id: str
    title: str
    stage: str = "investigate"
    question: str = ""
    symptoms: list[str] = field(default_factory=list)
    scope: Scope = field(default_factory=Scope)
    constraints: list[str] = field(default_factory=list)
    expected_output: list[str] = field(default_factory=list)
    stop_condition: str = ""
    tool_policy: ToolPolicy = field(default_factory=ToolPolicy)
    verification: Verification = field(default_factory=Verification)
    repo_url: str = ""
    repo_slug: str = ""
    branch: str = "main"
    workspace_branch: str = ""
    original_remote_url: str = ""
    created_at: str = field(default_factory=lambda: dt.datetime.now().isoformat(timespec="seconds"))
    stage_artifacts: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Task":
        scope = Scope(**data.get("scope", {}))
        tool_policy = ToolPolicy(**data.get("tool_policy", {}))
        verification = Verification(**data.get("verification", {}))
        fields = {k: v for k, v in data.items() if k not in {"scope", "tool_policy", "verification"}}
        return cls(scope=scope, tool_policy=tool_policy, verification=verification, **fields)

    def write(self, path: Path) -> None:
        path.write_text(yaml.safe_dump(self.to_dict(), sort_keys=False), encoding="utf-8")

    @classmethod
    def read(cls, path: Path) -> "Task":
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.from_dict(data)
