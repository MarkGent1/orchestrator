import asyncio
import sys
import os
import subprocess
from pathlib import Path

from ado_mcp_client import AdoMcpClient
from work_item_planning import WorkItemPlanner
from github_mcp_client import GithubMcpClient
from git_workflow import GitWorkflow
from validator import BuildTestValidator

from task_decomposer import decompose_task
from task_executor import execute_subtask
from task_memory import TaskMemory
from pr_enhancer import build_pr_description
from preflight_validator import preflight_validate


async def main():
    # ---------------------------------------------------------
    # CLI validation
    # ---------------------------------------------------------
    if len(sys.argv) != 4 or sys.argv[2] != "--repo":
        raise ValueError("Usage: python main.py <work_item_id> --repo <repo_path>")

    work_item_id = int(sys.argv[1])
    repo_path = Path(sys.argv[3]).resolve()

    # ---------------------------------------------------------
    # MCP server paths
    # ---------------------------------------------------------
    root = Path(__file__).parent.parent
    ado_server_path = str(root / "mcp-servers" / "ado" / "server.js")
    github_server_path = str(root / "mcp-servers" / "github" / "server.js")

    # ---------------------------------------------------------
    # Preflight Validator
    # ---------------------------------------------------------
    ok, message = preflight_validate(repo_path)
    if not ok:
        print(message)
        return

    print(message)

    # ---------------------------------------------------------
    # Clients
    # ---------------------------------------------------------
    ado = AdoMcpClient(ado_server_path)
    github = GithubMcpClient(github_server_path)
    planner = WorkItemPlanner(ado)
    gitflow = GitWorkflow(repo_path, github)

    # ---------------------------------------------------------
    # TEST MODE: COMMIT ALL CHANGES
    # ---------------------------------------------------------
    if os.environ.get("GITHUB_TEST_ONLY") == "1":
        print("Running in --commit-all GitHub test mode")

        branch_name = f"github-test-{work_item_id}"

        # Helper to run git commands
        def git_list(cmd):
            result = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return [p.strip() for p in result.stdout.splitlines() if p.strip()]

        # Detect all changed files
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
    # END TEST MODE
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # 1. Fetch Work Item + Plan
    # ---------------------------------------------------------
    plan_result = await planner.plan_work_item(work_item_id=work_item_id)
    plan = plan_result["plan"]
    plan["id"] = work_item_id  # ensure PR builder has an ID
    tasks = plan["tasks"]

    print(f"\nFetched Work Item {work_item_id}: {plan['title']}")
    print(f"Tasks: {[t['title'] for t in tasks]}")

    # ---------------------------------------------------------
    # 2. Create feature branch
    # ---------------------------------------------------------
    branch_name = gitflow.make_branch_name(work_item_id, plan["title"])
    print(f"\nCreating branch: {branch_name}")
    await gitflow.create_branch(branch_name)

    # ---------------------------------------------------------
    # 3. Task loop → decomposition → subtasks → commit
    # ---------------------------------------------------------
    task_memory = TaskMemory()

    for idx, task in enumerate(tasks, start=1):
        print(f"\n=== Task {idx}/{len(tasks)}: {task['title']} ===")

        # 1. Decompose into subtasks
        subtasks = await decompose_task(work_item_id, plan["title"], task)

        for sub in subtasks:
            print(f"--- Subtask: {sub['title']} ---")

            changed_files = await execute_subtask(
                repo_path,
                work_item_id,
                plan["title"],
                task,
                sub,
            )

            await gitflow.commit_task_changes(
                branch_name=branch_name,
                work_item_id=work_item_id,
                task=sub,
                changed_files=changed_files,
            )

            task_memory.add(task["title"], sub["title"], changed_files, notes="")

    # ---------------------------------------------------------
    # 3b. Verify build and test
    # ---------------------------------------------------------
    validator = BuildTestValidator(repo_path=repo_path, max_fix_attempts=3)
    ok, message = await validator.run_validation()

    if not ok:
        print(f"Build and test validation failed: {message}")
        return

    print(f"Build and test validation succeeded: {message}")

    # ---------------------------------------------------------
    # 4. Push branch
    # ---------------------------------------------------------
    print(f"\nPushing branch: {branch_name}")
    await gitflow.push_branch(branch_name)

    # ---------------------------------------------------------
    # 5. Open PR
    # ---------------------------------------------------------
    print("\nOpening Pull Request...")
    pr_body = build_pr_description(plan, task_memory, message)

    pr_url = await gitflow.open_pull_request(
        branch_name,
        plan["title"],
        pr_body,
    )

    print(f"PR created: {pr_url}")

    # ---------------------------------------------------------
    # 6. Link PR to Work Item
    # ---------------------------------------------------------
    print("\nLinking PR to Work Item...")
    await ado.link_pr(work_item_id, pr_url)

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


if __name__ == "__main__":
    asyncio.run(main())
