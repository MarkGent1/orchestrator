import asyncio
import sys
from pathlib import Path

from ado_mcp_client import AdoMcpClient
from work_item_planning import WorkItemPlanner
from github_mcp_client import GithubMcpClient
from git_workflow import GitWorkflow
from file_editing import apply_file_edits_for_task
from opencode_prompt_builder import build_opencode_prompt_for_task
from opencode_client import call_opencode


async def main():
    # ---------------------------------------------------------
    # CLI validation
    # ---------------------------------------------------------
    if len(sys.argv) < 3:
        raise ValueError("Usage: python main.py <work_item_id> --repo <repo_path>")

    work_item_id = int(sys.argv[1])

    if sys.argv[2] != "--repo" or len(sys.argv) < 4:
        raise ValueError("Usage: python main.py <work_item_id> --repo <repo_path>")

    repo_path = Path(sys.argv[3]).resolve()

    # ---------------------------------------------------------
    # MCP server paths
    # ---------------------------------------------------------
    root = Path(__file__).parent.parent
    ado_server_path = str(root / "mcp-servers" / "ado" / "server.js")
    github_server_path = str(root / "mcp-servers" / "github" / "server.js")

    # ---------------------------------------------------------
    # Clients
    # ---------------------------------------------------------
    ado = AdoMcpClient(ado_server_path)
    github = GithubMcpClient(github_server_path)
    planner = WorkItemPlanner(ado)
    git = GitWorkflow(repo_path, github)

    # ---------------------------------------------------------
    # 1. Fetch Work Item + Plan
    # ---------------------------------------------------------
    plan_result = await planner.plan_work_item(work_item_id=work_item_id)
    plan = plan_result["plan"]
    tasks = plan["tasks"]

    print(f"\nFetched Work Item {work_item_id}: {plan['title']}")
    print(f"Tasks: {[t['title'] for t in tasks]}")

    # ---------------------------------------------------------
    # 2. Create feature branch
    # ---------------------------------------------------------
    branch_name = git.make_branch_name(work_item_id, plan["title"])
    print(f"\nCreating branch: {branch_name}")
    await git.create_branch(branch_name)

    # ---------------------------------------------------------
    # 3. Task loop → OpenCode → file edits → commit
    # ---------------------------------------------------------
    for idx, task in enumerate(tasks, start=1):
        print(f"\n=== Task {idx}/{len(tasks)}: {task['title']} ===")

        # Build prompt for OpenCode
        prompt = await build_opencode_prompt_for_task(
            repo_path=repo_path,
            work_item_id=work_item_id,
            work_item_title=plan["title"],
            task=task,
        )

        # Call OpenCode (Claude API)
        file_edits = await call_opencode(prompt)

        # Apply edits to repo
        changed_files = apply_file_edits_for_task(repo_path, file_edits)

        # Commit changes
        await git.commit_task_changes(
            branch_name=branch_name,
            work_item_id=work_item_id,
            task=task,
            changed_files=changed_files,
        )

        print(f"Committed {len(changed_files)} file(s) for task: {task['title']}")

    # ---------------------------------------------------------
    # 4. Push branch
    # ---------------------------------------------------------
    print(f"\nPushing branch: {branch_name}")
    await git.push_branch(branch_name)

    # ---------------------------------------------------------
    # 5. Open PR
    # ---------------------------------------------------------
    print("\nOpening Pull Request...")
    pr_url = await git.open_pull_request(
        branch_name=branch_name,
        work_item_id=work_item_id,
        work_item_title=plan["title"],
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
