from __future__ import annotations

from pathlib import Path
import re
import subprocess


def run_git(args: list[str], cwd: Path | None = None, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        check=True,
        text=True,
        capture_output=capture_output,
    )


def slugify_repo(repo_url: str) -> str:
    cleaned = repo_url.strip().removesuffix(".git")
    cleaned = cleaned.replace(":", "/")
    parts = [p for p in cleaned.split("/") if p and p not in {"https", "http", "ssh", "git@github.com"}]
    if len(parts) >= 2:
        owner, repo = parts[-2], parts[-1]
    else:
        owner, repo = "repo", re.sub(r"[^a-zA-Z0-9._-]+", "-", cleaned)
    return f"{owner}__{repo}".lower()


def ensure_repo_cache(repo_url: str, cache_path: Path) -> None:
    if cache_path.exists():
        run_git(["remote", "update", "--prune"], cwd=cache_path)
        return
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    run_git(["clone", "--mirror", repo_url, str(cache_path)])


def clone_task_workspace(cache_path: Path, dest_repo_path: Path, branch: str) -> None:
    if dest_repo_path.exists():
        raise FileExistsError(f"Workspace repo already exists: {dest_repo_path}")
    dest_repo_path.parent.mkdir(parents=True, exist_ok=True)
    run_git(["clone", str(cache_path), str(dest_repo_path)])
    run_git(["checkout", branch], cwd=dest_repo_path)


def current_branch(repo_root: Path) -> str:
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root).stdout.strip()


def working_tree_summary(repo_root: Path) -> tuple[int, list[str]]:
    status = run_git(["status", "--short"], cwd=repo_root).stdout.splitlines()
    changed = [line.strip() for line in status if line.strip()]
    return len(changed), changed


def git_root(path: Path) -> Path:
    out = run_git(["rev-parse", "--show-toplevel"], cwd=path).stdout.strip()
    return Path(out)
