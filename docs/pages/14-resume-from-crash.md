# 14. Resume From a Crash

# 14.1 Overview

A full orchestrator run can involve dozens of model calls, several build/test cycles, and many minutes of wall-clock time. Before this feature, any failure partway through — a bad model response, a build that exhausts the FixLoop retry budget, a network blip talking to an MCP server, or the model proposing an illegal file path — meant the **entire run was lost**. Re-running meant re-planning the Work Item, re-creating the branch, and redoing every task and subtask from scratch, even the ones that had already succeeded and been committed.

The orchestrator now persists its progress as it goes and **automatically resumes from the exact point it left off** the next time you run the same command.

# 14.2 Where State Lives

Progress for a single `(repo, work item)` pair is written to:

    <orchestrator-dir>/.orchestrator-state/<safe-repo-key>-<work_item_id>.json

This lives **next to the orchestrator itself**, not inside the target repo — unlike `.orchestrator-tmp/`, which is wiped and recreated at the start of every run and therefore can't hold anything that needs to survive a crash. Because it's outside the target repo, there's nothing to `.gitignore` in your actual project repos; the orchestrator's own `.gitignore` already excludes `.orchestrator-state/`.

Each repo gets its own state file (keyed by its resolved absolute path), and each Work Item within a repo gets its own file, so runs against different repos or different Work Items never collide.

# 14.3 What Gets Persisted

`run_state.py` tracks, at the finest granularity that's safe to trust:

*   The feature branch name
*   The Work Item plan (title + top-level tasks)
*   Each task's subtask breakdown, once it has been decomposed for the first time
*   A `done` flag per task and per subtask
*   Whether build/test validation has already passed
*   The PR URL, once a PR has been opened

Subtask decomposition is deliberately persisted rather than recomputed on resume. The decomposition model call is not guaranteed to return the same breakdown twice — recomputing it could produce subtask titles that don't match what was already completed, making "already done" tracking meaningless. Once a task has been decomposed, that exact breakdown is reused for the lifetime of the run (including across resumes).

The state file is written atomically (via a temp file + rename) after every meaningful step, so a crash mid-write never leaves behind a half-written, unparseable file. If a state file somehow does become corrupted or unreadable, `RunState.load()` treats that the same as "no saved run" and starts fresh — this is a convenience feature, so it fails open rather than blocking you.

# 14.4 How Resume Works

You don't need to do anything differently. Just re-run the exact same command:

    python main.py <work_item_id> --repo <path_to_repo>

On startup, the orchestrator checks whether a state file already exists for that `(repo, work item)` pair:

*   **No existing state** → normal fresh run: plan the Work Item, create the branch, run every task.
*   **Existing state found** → the orchestrator prints a message telling you it's resuming, checks out the existing feature branch in your **real** repo (fetching it from `origin` first if it only exists remotely), and then:
    *   Skips Work Item planning entirely — the persisted plan and task list are reused.
    *   Skips branch creation — the branch already exists.
    *   For each task: if it's already marked done, skip it and its subtasks entirely (no model calls at all). If it has a persisted subtask breakdown, reuse it rather than re-decomposing.
    *   For each subtask: if already marked done, skip it. Otherwise execute it as normal.
    *   Skips build/test validation if it already passed in a previous run.
    *   Skips opening a new PR if one was already opened — the existing PR URL is reused when linking it to the Work Item.
*   Once everything completes successfully (PR opened and linked), the state file is deleted — there's nothing left to resume.

This means a crash three subtasks into Task 5 of a six-task plan costs you nothing but the failed subtask itself. Everything before it — including its git commits — is untouched.

# 14.5 A Real Example

This is exactly what happened in practice: a run crashed on the second subtask of a "Add unit tests" task because the model proposed a new test project under `src/` instead of reusing the existing one under `tests/`, and Clean Architecture enforcement correctly rejected it as an illegal new module (see [Troubleshooting](./9-troubleshooting.md)).

Re-running the identical command:

    python main.py 461 --repo D:\git\mav\mav-user-api-sdlc-poc

picked up exactly where it left off — same branch, same four already-committed tasks left alone, and only the one unfinished subtask re-executed. No re-planning, no duplicate commits, no lost work.

# 14.6 Starting Over Instead of Resuming

If you'd rather discard progress and start a Work Item completely fresh (e.g. you want a different plan, or the branch got into a bad state), delete its state file:

    <orchestrator-dir>/.orchestrator-state/<safe-repo-key>-<work_item_id>.json

The next run for that `(repo, work item)` pair will behave as if it had never been run before. You may also want to delete or reset the feature branch itself if you don't want to build on top of what was already committed.

# 14.7 Interaction With Existing ADO Child Tasks

Work Item planning itself is separately idempotent: if the Work Item already has child tasks linked (from a previous orchestrator run, or created manually), planning reuses them instead of asking the model again and creating duplicates. This is a best-effort, fails-open check — see [Module 1](./2-module-1.md) — and works alongside resume rather than replacing it: resume state is what lets an *in-progress* run pick up mid-task-loop; the ADO child-task check is what prevents a *completed or restarted* planning phase from generating a second, duplicate plan.

# 14.8 Crash-Containment Coverage

The crash-containment fix that lets a single invalid model edit be skipped instead of crashing the whole run (see [Troubleshooting](./9-troubleshooting.md)) covers both places an illegal path can come from: the main task-execution path (`task_executor.py`) and the FixLoop retry path (`validator.py` → `fix_loop.py`). Either one catches the `ValueError`, logs it clearly, and treats it as a failed attempt rather than a fatal crash — task execution moves on to the next subtask, and FixLoop moves on to its next retry attempt (or reports "fix loop exhausted" if attempts run out, same as any other unfixable error). Resume still applies on top of this: if a run does crash for some other reason, re-running the same command picks up from the first unfinished subtask as described above.

[<< Overview](../../README.md)
 |
[<< Model Capabilities](./13-model-capabilities.md)
