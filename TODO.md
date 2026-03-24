# TODO 

- Add command to clear task workspace
- Add some way to pass task name around the stages without specifying it
- Define when to use this tool vs use aider directly 
- Enforce the core workflow as non-optional: investigate -> plan -> execute, with each stage only able to run if the previous stage artifact exists.
 Persist real stage outputs to disk every time. Never save prompts or scaffolding text into 01-investigate.md, 02-plan.md, or 03-execute.md.
 Pass prior stage artifacts as the next stage’s input source of truth. Do not reconstruct context from the original question when a stage artifact exists.
 Hard-block code edits during investigate.
 Hard-block code edits during plan.
 Allow edits only during execute, and only within scoped files.
 Enforce scoped file boundaries at the CLI level, not by hoping the model obeys instructions.
 Fail loudly if no scoped files are set before execute.
 Show the scoped files clearly before every run so there is no ambiguity about what can be touched.
 Detect and reject out-of-scope file modifications after a run.
 Add a local diff audit after each run that shows exactly which files changed and whether any were out of scope.
 Add a “dry-run review” mode for execute that generates the execution artifact first without allowing code changes, so you can inspect intent before spending tokens.
 Add a local “apply patch” mode so the tool can generate a patch/diff for review before writing into the task repo.
 Add a task validate command that checks task integrity: artifact files exist, stage ordering is valid, scope exists, repo clone exists, git remotes are correct.
 Add a task status command that shows current stage, scoped files, modified files, artifact presence, and git branch/remotes.
 Add a task doctor command specifically for debugging broken workspaces and misconfigured repos.
 Validate git remotes on bootstrap and before every stage run: origin must point to GitHub, cache must point to the local mirror, and they must never be swapped.
 Add a repair command for git remotes so you do not keep fixing them manually.
 Add a deterministic workspace bootstrap that always creates the same folder structure and branch state.
 Ensure every task workspace starts from a clean clone and a known base branch/commit.
 Record the base commit SHA in task.yaml so you know exactly what the task started from.
 Record the current head SHA after each stage so you can detect accidental edits in non-edit stages.
 Add a local verification loop for dogfooding: bootstrap task, set scope, run investigate, inspect artifact, run plan, inspect artifact, run execute, inspect diff, run validation commands, inspect remotes.
 Add a one-command local dogfood workflow that automates the above verification loop inside this repo.
 Add a “replay task” command to rerun a task from saved artifacts without recreating the workspace.
 Add a “reset stage” command so you can wipe and rerun only investigate, only plan, or only execute.
 Add a “promote execution output to patch” step so execution results are reviewable before merge.
 Add a lightweight local review UI or TUI for artifacts + diffs + validation output. Right now your workflow is too scattered.
 Add a command to open the task workspace repo directly from the CLI.
 Add a command to open the task artifact directory directly from the CLI.
 Add a task summary view that shows question, scope, stage outputs, changed files, validation results, and spend.
 Track per-run model cost and accumulate total spend per task.
 Store spend in task.yaml and append run-level cost entries with timestamp, tool, stage, and model used.
 Track token usage per stage, not just total task cost.
 Track elapsed runtime per stage so you can see where the workflow is actually slow.
 Capture stdout/stderr logs for each stage run into task-local log files.
 Make logs readable. Right now debugging is probably harder than it should be because output is too raw.
 Save the exact command invocation metadata for each stage run so failures are reproducible.
 Add clear failure states in task.yaml: pending, running, completed, failed, blocked.
 Prevent a failed stage from silently allowing later stages to continue.
 Add structured validation rules for artifacts: investigate must contain findings/root cause, plan must contain ordered minimal steps, execute must contain what changed + how to verify.
 Add artifact quality checks so empty or obviously bad model output gets rejected before being saved.
 Add a post-run check that detects whether an artifact contains prompt text instead of actual output.
 Add a post-run check that detects whether investigate or plan caused file modifications and fail the run if so.
 Add a command to compare working tree changes before and after a stage and print a simple verdict: expected / unexpected.
 Add support for using the main repo as a local source of truth for testing without requiring the current pull-push-main-repo dance.
 Add a “sync back to parent repo” helper command for local dogfooding, so reviewing changes does not depend on manual git juggling.
 Add an optional mode that uses a local branch/worktree instead of a fresh clone for faster local iteration during dogfooding.
 Keep the isolated-clone model as default, but support a faster dev-only mode for testing the orchestrator on itself.
 Add a “review changed files in parent repo” shortcut, because your current workflow has too many context switches.
 Add a command that prints the exact git commands needed to merge task changes back safely.
 Add automated local smoke tests for the CLI commands themselves.
 Add integration tests that create a real task workspace, run all 3 stages, and assert that artifacts and repo state are correct.
 Add a regression test specifically for “investigate.md does not update.”
 Add a regression test specifically for “aider edits files during investigate/plan.”
 Add a regression test specifically for “origin remote incorrectly points to cache.”
 Add a regression test specifically for “stage N does not use stage N-1 output.”
 Add a regression test specifically for scope leakage outside allowed files.
 Add a regression test specifically for artifact containing prompt text instead of model output.
 Add fixture repos for testing common scenarios: clean repo, dirty repo, missing remote, out-of-scope edit, empty artifact, failed command.
 Add snapshot tests for task artifact generation so format changes are intentional.
 Add clear UX around task creation so task names, question, and scope are obvious and hard to mess up.
 Add template generation for task.yaml with sane defaults.
 Add task naming conventions so workspaces do not become garbage over time.
 Add a reusable “new task from current branch” flow for faster local dogfooding.
 Add support for task presets later, but do not touch that until the current workflow is reliable. Right now reliability matters more than portability.
 Add a simple ai-task dogfood command for this repo that creates a task against the orchestrator itself and walks the exact intended workflow.
 Add a “verify before merge” checklist command that prints: artifacts valid, no non-execute edits, no out-of-scope edits, remotes valid, tests passed, diff reviewed.
 Add a human-review gate before merge. The whole point is deterministic workflow, not blind automation.
 Add a concise README section for the dogfood loop in this project only.
 Add a separate later-state backlog for “use in other repos” so you stop mixing platform ambitions with core workflow fixes.
 Keep a ruthless distinction between “core invariant” and “nice-to-have.” If it does not protect deterministic execution, it is not core.
