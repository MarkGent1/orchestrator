import asyncio
import sys
from pathlib import Path

from ado_mcp_client import AdoMcpClient
from work_item_planning import WorkItemPlanner
from github_mcp_client import GithubMcpClient
from git_workflow import GitWorkflow
from file_editing import apply_file_edits_for_task
from opencode_prompt_builder import build_opencode_prompt_for_task
from opencode_client import call_opencode  # you’ll wire this to OpenCode Desktop API

async def main():
    if len(sys.argv) < 3:
        raise ValueError("Usage: python main.py <work_item_id> --repo <repo_path>")

    work_item_id = int(sys.argv[1])

    if sys.argv[2] != "--repo" or len(sys.argv) < 4:
        raise ValueError("Usage: python main.py <work_item_id> --repo <repo_path>")

    repo_path = Path(sys.argv[3]).resolve()

    ado_server_path = str(Path(__file__).parent.parent / "mcp-servers" / "ado" / "server.js")
    github_server_path = str(Path(__file__).parent.parent / "mcp-servers" / "github" / "server.js")

    ado = AdoMcpClient(ado_server_path)
    github = GithubMcpClient(github_server_path)
    planner = WorkItemPlanner(ado)
    git = GitWorkflow(repo_path, github)

    # 1. Fetch WI + plan
    plan_result = await planner.plan_work_item(work_item_id=work_item_id)
    plan = plan_result["plan"]
    tasks = plan["tasks"]
    
    # 2. Create feature branch
    branch_name = git.make_branch_name(work_item_id, plan["title"])
    await git.create_branch(branch_name)

    # 3. Loop through tasks → OpenCode → apply edits → commit
    for task in tasks:
        prompt = await build_opencode_prompt_for_task(
            repo_path=repo_path,
            work_item_id=work_item_id,
            work_item_title=plan["title"],
            task=task
        )

        file_edits = await call_opencode(prompt)

        await apply_file_edits_for_task(repo_path, file_edits)

        await git.commit_task_changes(
            branch_name=branch_name,
            work_item_id=work_item_id,
            task=task
        )

    # 4. Push branch
    await git.push_branch(branch_name)

    # 5. Open PR
    pr_url = await git.open_pull_request(
        branch_name=branch_name,
        work_item_id=work_item_id,
        work_item_title=plan["title"]
    )

    # 6. Link PR to Work Item in ADO
    await ado.link_pr(work_item_id, pr_url)

    print("\n=== RESULT ===")
    print({
        "work_item_id": work_item_id,
        "branch": branch_name,
        "pr_url": pr_url,
        "plan": plan
    })

if __name__ == "__main__":
    asyncio.run(main())
