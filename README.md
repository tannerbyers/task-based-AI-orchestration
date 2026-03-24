# ai-task-orchestrator

A thin orchestration layer for task/bug-based AI development.

This project creates isolated task workspaces from cached Git repositories, routes work through explicit stages, and stores task artifacts in a repeatable layout.

## Why this exists

Most AI coding spend gets wasted in three places:

1. vague prompts,
2. repo-wide context scanning,
3. muddled local state across long-lived worktrees.

This tool forces a task-first workflow:

- cache repositories once,
- create one workspace per task,
- store task metadata in a single file,
- keep investigation, planning, execution, and review separated.

## What is now usable

This repo is now at the point where you can dogfood it with Aider:

- cache a repo once and refresh it later,
- create a fresh workspace per task,
- write scoped stage prompts into task artifacts,
- launch `aider` against only the listed task files,
- keep task state and repo state isolated per bug or feature.

## Install

Run the install script:

```bash
bash install.sh
```

This will:
- Check for Python 3.11+
- Create a virtual environment (.venv)
- Install the package in the virtual environment
- Provide instructions to activate the environment

After installation, activate the virtual environment:

```bash
source .venv/bin/activate
```

Then you can use the `ai-task` command.

Note: If you prefer to run the script directly with `./install.sh`, you may need to make it executable first:

```bash
chmod +x install.sh
./install.sh
```

## Core commands

```bash
ai-task --help
ai-task repo add https://github.com/owner/repo.git
ai-task repo pull https://github.com/owner/repo.git
ai-task task bootstrap . dogfood-cli --question "Make task run more robust"
ai-task task create https://github.com/owner/repo.git bugfix-auth-reset --branch main
ai-task task files <task-path> src/auth.ts src/middleware.ts
ai-task task stage <task-path> investigate
ai-task task write-prompt <task-path>
ai-task task run <task-path> --tool aider
ai-task verify <task-path>
ai-task workspace list
```

## Daily dogfooding workflow

### 1. Bootstrap a task from the current repo

From inside this repo:

```bash
ai-task task bootstrap . improve-task-run \
  --question "Use aider to improve task run and prompt artifact handling"
```

This will:

- cache the current repo as a reusable mirror,
- create a new isolated workspace,
- clone a clean copy into `workspace/repo`,
- set up remotes (GitHub as "origin", cache as "cache"),
- create a task branch like `ai-task/2026-03-24-improve-task-run`.

### 2. Scope the task files

```bash
ai-task task files ~/.local/share/ai-task/workspaces/repo__ai-task-orchestrator/2026-03-24-improve-task-run \
  src/ai_task/cli.py \
  src/ai_task/models.py \
  README.md
```

### 3. Set the stage and inspect the prompt

```bash
ai-task task stage <task-path> investigate
ai-task task prompt <task-path>
```

### 4. Save the artifact and launch aider

```bash
ai-task task run <task-path> --tool aider
```

That command will:

- render the current stage prompt,
- save it into `task/01-investigate.md` or the matching stage file,
- launch `aider --message ... <scoped-files>` in the isolated workspace clone.

### 5. Advance the task

```bash
ai-task task stage <task-path> plan
ai-task task run <task-path> --tool aider

ai-task task stage <task-path> execute
ai-task task run <task-path> --tool aider
```

### 6. Verify

Put commands into `task/task.yaml`:

```yaml
verification:
  commands:
    - python -m pytest
    - python -m compileall src
```

Then run:

```bash
ai-task verify <task-path>
```

## Layout

```text
~/.cache/ai-task/repos/
  owner__repo.git/          # local mirror cache

~/.local/share/ai-task/workspaces/
  owner__repo/
    2026-03-24-bugfix-auth-reset/
      repo/                 # isolated git clone from cache
      task/
        task.yaml
        01-investigate.md
        02-plan.md
        03-execute.md
        04-review.md
        artifacts/
```

## Philosophy

This is intentionally thin.

It is not an agent runtime, queue, dashboard, or autonomous coding manager.
Its job is to impose operational boundaries:

- scope first,
- stage separation,
- cached repos,
- isolated task workspaces,
- repeatable artifacts,
- preserved context across stages.

## Features

- Preserves investigation results and explicit human decisions across plan and execute stages
- Maintains context between stages to ensure continuity in the development process
- Isolates task workspaces to prevent state pollution
- Enforces scoped file access to prevent repository-wide scanning
- Structures development through explicit stages (investigate, plan, execute, review)
- Properly persists stage results separately from prompts for better context preservation

## Immediate next additions worth building

- add `task publish` to push workspace branches,
- add `task diff` and `task status`,
- add tool adapters beyond Aider,
- add optional sparse checkout for large repos,
- add an onboarding template for team-wide task policy.
