from pathlib import Path
from typing import Dict, Any

from github_mcp_client import GithubMcpClient
from slugify import slugify

class GitWorkflow:
    def __init__(self, repo_path: Path, github: GithubMcpClient):
        self.repo_path = repo_path
        self.github = github

    def make_branch_name(self, work_item_id: int, title: str) -> str:
        slug = slugify(title)[:40]
        return f"feature/{work_item_id}-{slug}"

    async def create_branch(self, branch_name: str) -> None:
        await self.github.create_branch(self.repo_path, branch_name)

    async def commit_task_changes(
        self,
        branch_name: str,
        work_item_id: int,
        task: Dict[str, Any],
    ) -> None:
        message = (
            f"feat: Implement task — {task['title']}\n\n"
            f"Work Item: {work_item_id}\n"
            f"Task: {task['title']}\n"
            f"Description: {task.get('description', '')}\n"
        )

        # files list is built by file_editing.py; here we just call commitFiles
        # you can evolve this to pass explicit file list if needed
        await self.github.commit_files(
            self.repo_path,
            branch_name,
            message,
            files=[],  # placeholder; see file_editing.py
        )

    async def push_branch(self, branch_name: str) -> None:
        await self.github.push_branch(self.repo_path, branch_name)

    async def open_pull_request(
        self,
        branch_name: str,
        work_item_id: int,
        work_item_title: str,
    ) -> str:
        title = f"{work_item_title} (Work Item {work_item_id})"
        body = (
            f"This PR implements the plan for Work Item {work_item_id}.\n\n"
            f"Title: {work_item_title}\n"
        )
        return await self.github.open_pull_request(
            self.repo_path,
            branch_name,
            title,
            body,
        )
