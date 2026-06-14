from pathlib import Path
from typing import Dict, Any, List
import re

from github_mcp_client import GithubMcpClient

class GitWorkflow:
    def __init__(self, repo_path: Path, github: GithubMcpClient):
        self.repo_path = repo_path
        self.github = github

    @staticmethod
    def slugify(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        return text.strip("-")

    # ---------------------------------------------------------
    # Branch naming
    # ---------------------------------------------------------
    def make_branch_name(self, work_item_id: int, title: str) -> str:
        slug = self.slugify(title)[:40]
        return f"feature/{work_item_id}-{slug}"

    # ---------------------------------------------------------
    # Branch creation
    # ---------------------------------------------------------
    async def create_branch(self, branch_name: str) -> None:
        await self.github.create_branch(self.repo_path, branch_name)

    # ---------------------------------------------------------
    # Commit changes for a single task
    # ---------------------------------------------------------
    async def commit_task_changes(
        self,
        branch_name: str,
        work_item_id: int,
        task: Dict[str, Any],
        changed_files: List[Dict[str, Any]],
    ) -> None:
        message = (
            f"feat: Implement task — {task['title']}\n\n"
            f"Work Item: {work_item_id}\n"
            f"Task: {task['title']}\n"
            f"Description: {task.get('description', '')}\n"
        )

        await self.github.commit_files(
            repo_path=self.repo_path,
            branch_name=branch_name,
            message=message,
            files=changed_files,
        )

    # ---------------------------------------------------------
    # Push branch
    # ---------------------------------------------------------
    async def push_branch(self, branch_name: str) -> None:
        await self.github.push_branch(self.repo_path, branch_name)

    # ---------------------------------------------------------
    # Open PR
    # ---------------------------------------------------------
    async def open_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
    ) -> str:
        result = await self.github.open_pull_request(
            repo_path=self.repo_path,
            branch_name=branch_name,
            title=title,
            body=body,
        )
        return result
