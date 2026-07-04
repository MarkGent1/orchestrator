import argparse
import asyncio
import yaml
import os
import subprocess
import shutil
from pathlib import Path

from mcp_servers.ado_mcp_client import AdoMcpClient
from work_item_planning import WorkItemPlanner
from mcp_servers.github_mcp_client import GithubMcpClient
from git_workflow import GitWorkflow
from validator import BuildTestValidator

from task_decomposer import decompose_task
from task_executor import execute_subtask
from task_memory import TaskMemory
from pr_enhancer import build_pr_description
from preflight_validator import preflight_validate
from run_state import RunState

from utils.copy_repo import copy_repo_to_workspace
from utils.repo_scanner import build_module_map
from utils.tree_visualiser import print_tree
from architecture.enforcement import CleanArchitectureEnforcer

from model_constants import (
    DEFAULT_PLANNING_MODEL,
    DEFAULT_DECOMPOSITION_MODEL,
    DEFAULT_EXECUTION_MODEL,
    DEFAULT_FIXLOOP_MODEL,
)

# -------------------------------------------------------------
# python main.py 400 --repo D:\git\mav\mav-user-api-sdlc-poc
#   --planning-model gpt-5.4-mini
#   --fixloop-model gpt-5.4-mini
#   --decomposition-model gpt-5.4-mini
#   --execution-model gpt-5.4-mini
# -------------------------------------------------------------


def _checkout_branch_for_resume(repo_path: Path, branch_name: str) -> bool:
    """
    Checks out an existing feature branch in the REAL repo before the
    temp workspace is copied from it, so a resumed run's scratch copy
    reflects everything already committed in previous runs instead of
    the original base branch. Without this, the model would be shown
    stale code missing prior progress, risking edits that conflict
    with or duplicate already-completed work.

    Tries a plain checkout first, then falls back to fetching the
    branch from origin in case it only exists on the remote (e.g. a
    previous run pushed it but this is a fresh clone). Returns True on
    success, False if the branch genuinely could not be checked out.
    """
    def run_git(args):
        try:
            return subprocess.run(
                ["git", *args], cwd=repo_path, capture_output=True, text=True
            )
        except FileNotFoundError as ex:
            print(f"git is not available on PATH: {ex}")
            return None

    result = run_git(["checkout", branch_name])
    if result is not None and result.returncode == 0:
        return True

    run_git(["fetch", "origin", branch_name])
    result = run_git(["checkout", branch_name])
    if result is not None and result.returncode == 0:
        return True

    if result is not None:
        print(f"git checkout output:\n{result.stderr}")
    return False


async def main():
    # ---------------------------------------------------------
    # CLI validation
    # ---------------------------------------------------------
    parser = argparse.ArgumentParser()

    parser.add_argument("work_item_id", type=int)
    parser.add_argument("--repo", required=True)

    # NOTE: these default to None (not the hardcoded model constants) so
    # the fallback chain below can tell "not passed on the CLI" apart
    # from "explicitly passed". If these defaulted to the model
    # constants directly, `args.planning_model` etc. would always be
    # truthy and the values loaded from models.yaml a few lines down
    # would silently never be used.
    parser.add_argument("--planning-model", default=None)
    parser.add_argument("--fixloop-model", default=None)
    parser.add_argument("--decomposition-model", default=None)
    parser.add_argument("--execution-model", default=None)

    args = parser.parse_args()

    work_item_id = args.work_item_id
    repo_path = Path(args.repo).resolve()

    # ---------------------------------------------------------
    # Load default model config from models.yaml
    # ---------------------------------------------------------
    models_yaml_path = Path(__file__).parent / "models.yaml"

    if models_yaml_path.exists():
        with open(models_yaml_path, "r", encoding="utf-8") as f:
            default_model_config = yaml.safe_load(f)
    else:
        default_model_config = {
            "planning_model": DEFAULT_PLANNING_MODEL,
            "decomposition_model": DEFAULT_DECOMPOSITION_MODEL,
            "execution_model": DEFAULT_EXECUTION_MODEL,
            "fixloop_model": DEFAULT_FIXLOOP_MODEL,
        }

    # ---------------------------------------------------------
    # CLI overrides YAML defaults, which override hardcoded defaults
    # ---------------------------------------------------------
    model_config = {
        "planning_model": args.planning_model or default_model_config.get("planning_model", DEFAULT_PLANNING_MODEL),
        "fixloop_model": args.fixloop_model or default_model_config.get("fixloop_model", DEFAULT_FIXLOOP_MODEL),
        "decomposition_model": args.decomposition_model or default_model_config.get("decomposition_model", DEFAULT_DECOMPOSITION_MODEL),
        "execution_model": args.execution_model or default_model_config.get("execution_model", DEFAULT_EXECUTION_MODEL),
    }

    # ---------------------------------------------------------
    # Startup Banner: Show Selected Models
    # ---------------------------------------------------------
    print("\n==================== ORCHESTRATOR MODEL CONFIG ====================")
    print(f"Planning Model:      {model_config['planning_model']}")
    print(f"Decomposition Model: {model_config['decomposition_model']}")
    print(f"Execution Model:     {model_config['execution_model']}")
    print(f"FixLoop Model:       {model_config['fixloop_model']}")
    print("====================================================================\n")

    # ---------------------------------------------------------
    # MCP server paths
    # ---------------------------------------------------------
    root = Path(__file__).parent.parent
    ado_server_path = str(root / "mcp-servers" / "ado" / "server.js")
    github_server_path = str(root / "mcp-servers" / "github" / "server.js")

    # ---------------------------------------------------------
    # Resume check
    #
    # Done BEFORE touching the temp workspace: if a previous run for
    # this (repo, work item) got partway through and crashed, this
    # picks the plan and progress back up instead of starting over
    # from Work Item planning and Task 1. See run_state.py.
    # ---------------------------------------------------------
    run_state = RunState.load(repo_path, work_item_id)
    resuming = run_state is not None

    if resuming:
        print(
            f"\nFound previous progress for Work Item {work_item_id} on branch "
            f"'{run_state.branch_name}' -- resuming instead of starting over.\n"
        )

        # The temp workspace is about to be recreated from whatever is
        # currently checked out in the real repo. On a fresh run that's
        # fine (it's the base branch). On a resume it needs to be the
        # feature branch that prior runs already committed to,
        # otherwise the model would be working from stale code missing
        # everything already done.
        if not _checkout_branch_for_resume(repo_path, run_state.branch_name):
            print(
                f"Could not check out existing branch '{run_state.branch_name}' "
                f"in {repo_path}. Aborting resume so we don't risk generating "
                f"edits against the wrong base.\n"
                f"Check out that branch manually and re-run, or delete "
                f"{run_state.path} to start this Work Item over from scratch."
            )
            return

    # ---------------------------------------------------------
    # Temp workspace
    # ---------------------------------------------------------
    temp_workspace = repo_path / ".orchestrator-tmp"
    if temp_workspace.exists():
        shutil.rmtree(temp_workspace, ignore_errors=True)
    temp_workspace.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # Copy real repo into temp workspace
    # ---------------------------------------------------------
    copy_repo_to_workspace(repo_path, temp_workspace)

    print("=== TEMP WORKSPACE TREE ===")
    print_tree(temp_workspace, max_depth=3)

    # ---------------------------------------------------------
    # Preflight Validator (run on temp workspace)
    # ---------------------------------------------------------
    ok, message = preflight_validate(temp_workspace)
    if not ok:
        print(message)
        return
    print(message)

    # ---------------------------------------------------------
    # Detect repo type (backend or frontend)
    # ---------------------------------------------------------
    from repo_type import detect_repo_type
    repo_type = detect_repo_type(temp_workspace)

    # ---------------------------------------------------------
    # Clean Architecture Enforcer
    # ---------------------------------------------------------
    enforcer = CleanArchitectureEnforcer(temp_workspace, repo_type)

    print("Detected modules:")
    print(enforcer.describe_modules())

    # ---------------------------------------------------------
    # MODULE DISCOVERY
    # ---------------------------------------------------------
    module_root = temp_workspace / "src"
    module_map = build_module_map(module_root)

    print("Module Map:")
    for name, info in module_map.items():
        print(f"- {name}: folders={info['folders']}")

    # ---------------------------------------------------------
    # Clients
    #
    # Both clients spawn a long-lived Node child process. Everything
    # from here on is wrapped in try/finally so those processes are
    # always terminated on the way out -- including when a task
    # raises partway through the run. Without this, every run (and
    # especially every crash/retry during development) leaks a node
    # process that keeps running in the background indefinitely.
    # ---------------------------------------------------------
    ado = AdoMcpClient(ado_server_path)
    github = GithubMcpClient(github_server_path)

    try:
        planner = WorkItemPlanner(ado, model_config)

        # GitWorkflow MUST operate on the real repo, not temp workspace
        gitflow = GitWorkflow(repo_path, github, repo_type)

        # ---------------------------------------------------------
        # TEST MODE: COMMIT ALL CHANGES
        # ---------------------------------------------------------
        if os.environ.get("GITHUB_TEST_ONLY") == "1":
            print("Running in --commit-all GitHub test mode")

            branch_name = f"feature/github-test-{work_item_id}"

            def git_list(cmd):
                result = subprocess.run(
                    cmd,
                    cwd=repo_path,
                    capture_output=True,
                    text=True
                )
                return [p.strip() for p in result.stdout.splitlines() if p.strip()]

            modified = git_list(["git", "diff", "--name-only"])
            staged = git_list(["git", "diff", "--cached", "--name-only"])
            untracked = git_list(["git", "ls-files", "--others", "--exclude-standard"])
            deleted = git_list(["git", "ls-files", "--deleted"])

            all_paths = set(modified + staged + untracked + deleted)

            if not all_paths:
                raise RuntimeError("No changed files detected for --commit-all mode")

            changed_files = []
            for p in all_paths:
                full = repo_path / p

                if p in deleted:
                    changed_files.append({"path": p, "content": None})
                    continue

                content = full.read_text()
                changed_files.append({"path": p, "content": content})

            print(f"Creating branch: {branch_name}")
            await gitflow.create_branch(branch_name)

            print("Committing ALL detected file changes")
            await gitflow.commit_task_changes(
                branch_name=branch_name,
                work_item_id=work_item_id,
                task={"title": "Commit All"},
                changed_files=changed_files,
            )

            print("Pushing branch")
            await gitflow.push_branch(branch_name)

            print("Opening PR")
            pr_url = await gitflow.open_pull_request(
                branch_name,
                f"GitHub Commit-All Test {work_item_id}",
                "This PR was created using --commit-all mode."
            )

            print("PR created:", pr_url)
            return

        # ---------------------------------------------------------
        # 1. Fetch Work Item + Plan (or resume an existing plan)
        # ---------------------------------------------------------
        if resuming:
            branch_name = run_state.branch_name
            plan = {
                "id": work_item_id,
                "repo_type": repo_type,
                "title": run_state.plan_title,
                "tasks": [
                    {"title": t["title"], "description": t["description"]}
                    for t in run_state.tasks
                ],
            }
        else:
            plan_result = await planner.plan_work_item(work_item_id=work_item_id)
            plan = plan_result["plan"]
            plan["id"] = work_item_id
            # Used by build_pr_description() so the PR summary correctly
            # says "backend"/"frontend"/"fullstack" instead of always
            # defaulting to "backend".
            plan["repo_type"] = repo_type

        tasks = plan["tasks"]

        print(f"\nFetched Work Item {work_item_id}: {plan['title']}")
        print(f"Tasks: {[t['title'] for t in tasks]}")

        # ---------------------------------------------------------
        # 2. Create feature branch (skip if resuming -- it already
        #    exists and was just checked out above)
        # ---------------------------------------------------------
        if resuming:
            print(f"\nUsing existing branch: {branch_name}")
        else:
            branch_name = gitflow.make_branch_name(work_item_id, plan["title"])
            print(f"\nCreating branch: {branch_name}")
            await gitflow.create_branch(branch_name)

            run_state = RunState(repo_path, work_item_id)
            run_state.init_plan(branch_name, plan["title"], tasks)

        # ---------------------------------------------------------
        # 3. Task loop → decomposition → subtasks → commit
        #
        # Tasks and subtasks already marked done in run_state (from a
        # previous run) are skipped entirely rather than re-executed.
        # Subtask decomposition is only ever computed once per task
        # and then persisted -- re-decomposing on resume could return
        # a different breakdown than last time, since it's a fresh
        # model call, which would make "already done" matching by
        # title meaningless.
        # ---------------------------------------------------------
        task_memory = TaskMemory()

        for idx, task in enumerate(tasks, start=1):
            task_state = run_state.get_task(task["title"])

            if task_state and task_state["done"]:
                print(f"\n=== Task {idx}/{len(tasks)}: {task['title']} (already completed, skipping) ===")
                for s in (task_state.get("subtasks") or []):
                    task_memory.add(task["title"], s["title"], [], notes="(completed in a previous run)")
                continue

            print(f"\n=== Task {idx}/{len(tasks)}: {task['title']} ===")

            if task_state and task_state.get("subtasks"):
                subtasks = [
                    {"title": s["title"], "description": s["description"]}
                    for s in task_state["subtasks"]
                ]
            else:
                subtasks = await decompose_task(
                    work_item_id,
                    plan["title"],
                    task,
                    repo_type,
                    model_config)
                run_state.set_task_subtasks(task["title"], subtasks)
                task_state = run_state.get_task(task["title"])

            for sub in subtasks:
                if run_state.is_subtask_done(task["title"], sub["title"]):
                    print(f"--- Subtask: {sub['title']} (already completed, skipping) ---")
                    task_memory.add(task["title"], sub["title"], [], notes="(completed in a previous run)")
                    continue

                print(f"--- Subtask: {sub['title']} ---")

                changed_files = await execute_subtask(
                    repo_path,
                    temp_workspace,
                    work_item_id,
                    plan["title"],
                    task,
                    sub,
                    repo_type,
                    enforcer,
                    model_config
                )

                if changed_files:
                    await gitflow.commit_task_changes(
                        branch_name=branch_name,
                        work_item_id=work_item_id,
                        task=sub,
                        changed_files=changed_files,
                    )
                else:
                    print(f"--- Subtask '{sub['title']}' produced no file changes; skipping commit ---")

                task_memory.add(task["title"], sub["title"], changed_files, notes="")
                run_state.mark_subtask_done(task["title"], sub["title"])

        # ---------------------------------------------------------
        # 3b. Verify build and test
        # ---------------------------------------------------------
        if resuming and run_state.validated:
            print("\nBuild and test validation already passed in a previous run; skipping.")
            ok, message = True, "Already validated in a previous run"
        else:
            validator = BuildTestValidator(
                repo_path=repo_path,
                temp_workspace=temp_workspace,
                max_fix_attempts=3,
                repo_type=repo_type,
                enforcer=enforcer,
                model_config=model_config
            )

            ok, message = await validator.run_validation()

            if not ok:
                print(f"Build and test validation failed: {message}")
                return

            print(f"Build and test validation succeeded: {message}")
            run_state.mark_validated()

        # ---------------------------------------------------------
        # 4/5. Push branch + open PR (skip if a previous run already
        #      got a PR opened)
        # ---------------------------------------------------------
        if run_state.pr_url:
            print(f"\nPR already opened in a previous run: {run_state.pr_url}")
            pr_url = run_state.pr_url
        else:
            print(f"\nPushing branch: {branch_name}")
            await gitflow.push_branch(branch_name)

            print("\nOpening Pull Request...")
            pr_body = build_pr_description(plan, task_memory, message)

            pr_url = await gitflow.open_pull_request(
                branch_name,
                plan["title"],
                pr_body,
            )

            print(f"PR created: {pr_url}")
            run_state.mark_pr_opened(pr_url)

        # ---------------------------------------------------------
        # 6. Link PR to Work Item
        # ---------------------------------------------------------
        print("\nLinking PR to Work Item...")
        await ado.link_pr(work_item_id, pr_url)

        # Fully done -- nothing left to resume.
        run_state.clear()

        # ---------------------------------------------------------
        # Final output
        # ---------------------------------------------------------
        print("\n=== COMPLETE ===")
        print({
            "work_item_id": work_item_id,
            "branch": branch_name,
            "pr_url": pr_url,
            "plan": plan,
        })

    finally:
        # Always terminate both MCP server child processes, whether
        # this run succeeded, failed validation, or raised partway
        # through a task. Previously nothing ever called close() on
        # these, so every invocation (successful or not) leaked a
        # long-lived "node" process.
        ado.close()
        github.close()


if __name__ == "__main__":
    asyncio.run(main())
