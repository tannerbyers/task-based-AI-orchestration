from __future__ import annotations

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .models import Task


class PromptRenderer:
    def __init__(self, template_dir: Path):
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, stage: str, task: Task) -> str:
        template = self.env.get_template(f"{stage}.j2")
        return template.render(task=task)
