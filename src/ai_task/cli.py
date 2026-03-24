from __future__ import annotations

from pathlib import Path
import datetime as dt
import shlex
import subprocess

import typer
from rich.console import Console
from rich.table import Table

from .config import get_paths
from .gitops import (
    clone_task_workspace,
    current_branch,
    ensure_repo_cache,
    git_root,
    slugify_repo,
    working_tree_summary,
)
from .models import Task, DEFAULT_STAGE_ARTIFACTS
from .prompting import PromptRenderer

app = typer.Typer(help="Thin orchestration layer for task-based AI development")
repo_app = typer.Typer(help="Manage cached repositories")
task_app = typer.Typer(help="Manage task workspaces")
workspace_app = typer.Typer(help="Inspect workspaces")
app.add_typer(repo_app, name="repo")
app.add_typer(task_app, name="task")
app.add_typer(workspace_app, name="workspace")
console = Console()


AIDER_SENTINEL = "# --- ai-task generated prompt below ---"


def _template_dir() -> Path:
    return Path(__file__).parent / "templates"


def _task_yaml(task_path: Path) -> Path:
    if task_path.name == "task.yaml":
        return task_path
    return task_path / "task" / "task.yaml"


def _workspace_root_from_any(task_path: Path) -> Path:
    if task_path.name == "task.yaml":
        return task_path.parent.parent
    return task_path


def _workspace_task_dir(task_path: Path) -> Path:
    return _workspace_root_from_any(task_path) / "task"


def _workspace_repo(task_path: Path) -> Path:
    return _workspace_root_from_any(task_path) / "repo"


def _load_task(task_path: Path) -> Task:
    return Task.read(_task_yaml(task_path))


def _render_stage(task: Task, stage: str) -> str:
    renderer = PromptRenderer(_template_dir())
    rendered = renderer.render(stage, task)
    
    # Add context from previous stages if available
    if stage in ["plan", "execute", "review"]:
        previous_context = []
        
        if stage in ["plan", "execute", "review"] and "investigate" in task.stage_results:
            previous_context.append("\n## Investigation Results\n\n" + task.stage_results["investigate"])
            
        if stage in ["execute", "review"] and "plan" in task.stage_results:
            previous_context.append("\n## Plan\n\n" + task.stage_results["plan"])
            
        if stage == "review" and "execute" in task.stage_results:
            previous_context.append("\n## Execution\n\n" + task.stage_results["execute"])
            
        if previous_context:
            rendered += "\n\n# Previous Stage Context\n" + "".join(previous_context)
    
    return rendered


def _write_stage_artifact(task_path: Path, stage: str, content: str) -> Path:
    task_dir = _workspace_task_dir(task_path)
    artifact = task_dir / DEFAULT_STAGE_ARTIFACTS[stage]
    artifact.write_text(content.rstrip() + "\n", encoding="utf-8")
    return artifact


@repo_app.command("add")
def repo_add(repo_url: str):
    """Cache or refresh a Git repository mirror."""
    paths = get_paths()
    slug = slugify_repo(repo_url)
    cache_path = paths.repo_cache_root / f"{slug}.git"
    ensure_repo_cache(repo_url, cache_path)
    console.print(f"[green]Cached:[/green] {repo_url}")
    console.print(f"[dim]{cache_path}[/dim]")


@repo_app.command("pull")
def repo_pull(repo_url: str):
    """Refresh an existing cached mirror."""
    paths = get_paths()
    slug = slugify_repo(repo_url)
    cache_path = paths.repo_cache_root / f"{slug}.git"
    if not cache_path.exists():
        raise typer.BadParameter("Repo is not cached yet. Run `ai-task repo add <repo-url>` first.")
    ensure_repo_cache(repo_url, cache_path)
    console.print(f"[green]Refreshed:[/green] {cache_path}")


@repo_app.command("list")
def repo_list():
    """List cached repository mirrors."""
    paths = get_paths()
    table = Table(title="Cached repositories")
    table.add_column("Name")
    table.add_column("Path")
    found = False
    for item in sorted(paths.repo_cache_root.glob("*.git")):
        found = True
        table.add_row(item.stem, str(item))
    if not found:
        console.print("No cached repositories found.")
        return
    console.print(table)


@task_app.command("bootstrap")
def task_bootstrap(
    repo_path: Path = typer.Argument(..., exists=True, file_okay=False, dir_okay=True),
    task_name: str = typer.Argument(...),
    branch: str = typer.Option("", help="Source branch to mirror. Defaults to current branch."),
    question: str = typer.Option("", help="Initial task question"),
):
    """Cache a local repo and create a task workspace from it."""
    repo_root = git_root(repo_path.resolve())
    repo_url = str(repo_root)
    effective_branch = branch or current_branch(repo_root)
    task_create(repo_url=repo_url, task_name=task_name, branch=effective_branch, question=question)


@task_app.command("create")
def task_create(
    repo_url: str,
    task_name: str,
    branch: str = typer.Option("main", help="Branch to checkout in the task workspace"),
    question: str = typer.Option("", help="Initial task question"),
):
    """Create an isolated task workspace from a cached repository."""
    paths = get_paths()
    slug = slugify_repo(repo_url)
    cache_path = paths.repo_cache_root / f"{slug}.git"
    ensure_repo_cache(repo_url, cache_path)

    date_prefix = dt.date.today().isoformat()
    task_slug = task_name.strip().lower().replace(" ", "-")
    workspace_path = paths.workspace_root / slug / f"{date_prefix}-{task_slug}"
    repo_path = workspace_path / "repo"
    task_dir = workspace_path / "task"
    task_dir.mkdir(parents=True, exist_ok=True)
    clone_task_workspace(cache_path, repo_path, branch)
    
    # Set up remotes - cache as "cache" and original repo as "origin"
    # Always rename the initial remote to "cache" and set original repo as "origin"
    subprocess.run(["git", "remote", "rename", "origin", "cache"], cwd=repo_path, check=True)
    subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=repo_path, check=True)

    workspace_branch = f"ai-task/{date_prefix}-{task_slug}"
    subprocess.run(["git", "checkout", "-b", workspace_branch], cwd=repo_path, check=True)

    task = Task(
        id=f"TASK-{date_prefix}-{task_slug}",
        title=task_name,
        question=question,
        repo_url=repo_url,
        repo_slug=slug,
        branch=branch,
        workspace_branch=workspace_branch,
        original_remote_url=repo_url,
        constraints=[
            "do not scan the entire repo",
            "stay within listed files unless explicitly updated",
            "separate investigation from execution",
        ],
        expected_output=[
            "clear result for the current stage",
            "smallest next action",
        ],
        stop_condition="Produce the requested stage output without expanding scope.",
    )
    task.write(task_dir / "task.yaml")
    (task_dir / "artifacts").mkdir(exist_ok=True)
    for filename in DEFAULT_STAGE_ARTIFACTS.values():
        (task_dir / filename).touch(exist_ok=True)

    console.print(f"[green]Created workspace:[/green] {workspace_path}")
    console.print(f"[green]Repo:[/green] {repo_path}")
    console.print(f"[green]Task file:[/green] {task_dir / 'task.yaml'}")
    console.print(f"[green]Workspace branch:[/green] {workspace_branch}")


@task_app.command("files")
def task_files(task_path: Path, files: list[str]):
    """Add or replace relative file scope for a task."""
    task = _load_task(task_path)
    repo_root = _workspace_repo(task_path)
    normalized: list[str] = []
    for file in files:
        rel = Path(file)
        if rel.is_absolute():
            try:
                rel = rel.relative_to(repo_root)
            except ValueError as exc:
                raise typer.BadParameter(f"Absolute path must be inside task repo: {file}") from exc
        normalized.append(rel.as_posix())
    task.scope.files = normalized
    task.write(_task_yaml(task_path))
    console.print(f"[green]Updated file scope:[/green] {len(normalized)} file(s)")


@task_app.command("stage")
def task_stage(task_path: Path, stage: str):
    """Update the active task stage."""
    if stage not in DEFAULT_STAGE_ARTIFACTS:
        raise typer.BadParameter(f"Invalid stage: {stage}")
    task = _load_task(task_path)
    
    # Save the current stage artifact content if it exists
    current_stage = task.stage
    if current_stage in DEFAULT_STAGE_ARTIFACTS:
        artifact_path = _workspace_task_dir(task_path) / DEFAULT_STAGE_ARTIFACTS[current_stage]
        if artifact_path.exists():
            content = artifact_path.read_text(encoding="utf-8")
            if content.strip():  # Only save non-empty artifacts
                # Store the content as a result, not the prompt
                task.stage_results[current_stage] = content
    
    task.stage = stage
    task.write(_task_yaml(task_path))
    console.print(f"[green]Stage set to:[/green] {stage}")


@task_app.command("show")
def task_show(task_path: Path):
    """Display task metadata."""
    task = _load_task(task_path)
    repo_root = _workspace_repo(task_path)
    changed_count, changed = working_tree_summary(repo_root)
    table = Table(title=task.title)
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("ID", task.id)
    table.add_row("Stage", task.stage)
    table.add_row("Repo", task.repo_url)
    table.add_row("Base branch", task.branch)
    table.add_row("Workspace branch", task.workspace_branch or "-")
    table.add_row("Files", "\n".join(task.scope.files) or "-")
    table.add_row("Question", task.question or "-")
    table.add_row("Stop condition", task.stop_condition or "-")
    table.add_row("Changed files", str(changed_count))
    table.add_row("Status", "\n".join(changed[:10]) or "clean")
    
    # Show completed stages
    completed_stages = list(task.stage_results.keys())
    if completed_stages:
        table.add_row("Completed stages", ", ".join(completed_stages))
    
    console.print(table)


@task_app.command("validate")
def task_validate(task_path: Path):
    """Validate task file requirements and scope size."""
    task = _load_task(task_path)
    errors: list[str] = []
    if not task.question.strip():
        errors.append("question is required")
    if not task.stop_condition.strip():
        errors.append("stop_condition is required")
    if len(task.scope.files) > task.tool_policy.max_files:
        errors.append(
            f"scope.files exceeds max_files ({len(task.scope.files)} > {task.tool_policy.max_files})"
        )
    if task.stage not in DEFAULT_STAGE_ARTIFACTS:
        errors.append(f"invalid stage: {task.stage}")

    if errors:
        for err in errors:
            console.print(f"[red]ERROR:[/red] {err}")
        raise typer.Exit(code=1)
    console.print("[green]Task is valid.[/green]")


@task_app.command("prompt")
def task_prompt(task_path: Path, stage: str = typer.Argument("")):
    """Render a stage prompt from the task file."""
    task = _load_task(task_path)
    active_stage = stage or task.stage
    rendered = _render_stage(task, active_stage)
    console.print(rendered)


@task_app.command("write-prompt")
def task_write_prompt(task_path: Path, stage: str = typer.Argument("")):
    """Render and save the stage prompt artifact for the task."""
    task = _load_task(task_path)
    active_stage = stage or task.stage
    rendered = _render_stage(task, active_stage)
    artifact = _write_stage_artifact(task_path, active_stage, rendered)
    console.print(f"[green]Wrote:[/green] {artifact}")


@task_app.command("run")
def task_run(
    task_path: Path,
    stage: str = typer.Argument(""),
    tool: str = typer.Option("aider", help="Tool adapter to use. Currently supports: aider, print"),
    yes: bool = typer.Option(False, "--yes", help="Skip confirmation before launching the tool"),
    message: str = typer.Option("", help="Override the rendered stage prompt"),
):
    """Write the stage artifact and launch a bounded tool command."""
    task = _load_task(task_path)
    active_stage = stage or task.stage
    if active_stage not in DEFAULT_STAGE_ARTIFACTS:
        raise typer.BadParameter(f"Invalid stage: {active_stage}")

    task.stage = active_stage
    rendered = message or _render_stage(task, active_stage)
    artifact = _write_stage_artifact(task_path, active_stage, rendered)
    
    # Save the rendered prompt to the task's stage artifacts
    task.stage_artifacts[active_stage] = rendered
    # Don't overwrite existing stage results when running a tool
    task.write(_task_yaml(task_path))
    
    repo_root = _workspace_repo(task_path)

    if tool == "print":
        console.print(rendered)
        return

    if tool != "aider":
        raise typer.BadParameter("Unsupported tool. Use --tool aider or --tool print.")

    if not task.scope.files:
        raise typer.BadParameter("task.scope.files is empty. Set scoped files before running aider.")

    prompt_text = (
        "Read the task artifact below and follow it exactly. "
        "Do not expand scope beyond the listed files.\n\n"
        f"{AIDER_SENTINEL}\n{rendered}\n"
    )
    cmd = ["aider", "--message", prompt_text, *task.scope.files]

    console.print(f"[green]Artifact:[/green] {artifact}")
    console.print(f"[green]Repo:[/green] {repo_root}")
    console.print(f"[green]Command:[/green] {' '.join(shlex.quote(part) for part in cmd)}")

    if not yes:
        proceed = typer.confirm("Launch aider now?", default=True)
        if not proceed:
            raise typer.Exit(code=0)

    subprocess.run(cmd, cwd=repo_root, check=True)


@workspace_app.command("list")
def workspace_list():
    """List task workspaces."""
    paths = get_paths()
    table = Table(title="Task workspaces")
    table.add_column("Repo")
    table.add_column("Workspace")
    found = False
    for repo_dir in sorted(paths.workspace_root.iterdir()):
        if not repo_dir.is_dir():
            continue
        for workspace in sorted(repo_dir.iterdir()):
            if workspace.is_dir():
                found = True
                table.add_row(repo_dir.name, str(workspace))
    if not found:
        console.print("No workspaces found.")
        return
    console.print(table)


@app.command("verify")
def verify(task_path: Path):
    """Run verification commands from a task file inside the workspace repo."""
    task = _load_task(task_path)
    repo_root = _workspace_repo(task_path)
    if not task.verification.commands:
        console.print("No verification commands configured.")
        raise typer.Exit(code=1)
    for cmd in task.verification.commands:
        console.print(f"[cyan]Running:[/cyan] {cmd}")
        result = subprocess.run(cmd, cwd=repo_root, shell=True)
        if result.returncode != 0:
            raise typer.Exit(code=result.returncode)
    console.print("[green]Verification complete.[/green]")
