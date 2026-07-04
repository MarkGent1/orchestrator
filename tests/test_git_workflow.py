import asyncio
from pathlib import Path

from git_workflow import GitWorkflow


class FakeGithubClient:
    def __init__(self):
        self.calls = []

    async def create_branch(self, repo_path, branch_name):
        self.calls.append(("create_branch", repo_path, branch_name))

    async def commit_files(self, repo_path, branch_name, message, files):
        self.calls.append(("commit_files", repo_path, branch_name, message, files))

    async def push_branch(self, repo_path, branch_name):
        self.calls.append(("push_branch", repo_path, branch_name))

    async def open_pull_request(self, repo_path, branch_name, title, body):
        self.calls.append(("open_pull_request", repo_path, branch_name, title, body))
        return "https://github.com/org/repo/pull/1"


def test_slugify_lowercases_and_replaces_non_alnum():
    assert GitWorkflow.slugify("Add UsersController! (v2)") == "add-userscontroller-v2"


def test_slugify_strips_leading_trailing_dashes():
    assert GitWorkflow.slugify("---Weird Title---") == "weird-title"


def test_make_branch_name_includes_id_and_truncated_slug():
    gw = GitWorkflow(Path("/repo"), FakeGithubClient(), "backend")
    name = gw.make_branch_name(404, "A" * 100)
    assert name.startswith("feature/404-")
    slug_part = name.split("-", 1)[1]
    assert len(slug_part) <= 40


def test_create_branch_delegates_to_github_client():
    client = FakeGithubClient()
    repo_path = Path("/repo")
    gw = GitWorkflow(repo_path, client, "backend")
    asyncio.run(gw.create_branch("feature/404-thing"))
    assert client.calls == [("create_branch", str(repo_path), "feature/404-thing")]


def test_commit_task_changes_builds_message_and_delegates():
    client = FakeGithubClient()
    gw = GitWorkflow(Path("/repo"), client, "backend")
    task = {"title": "Sub A", "description": "desc"}
    changed_files = [{"path": "a.cs", "content": "x"}]

    asyncio.run(gw.commit_task_changes("feature/404-thing", 404, task, changed_files))

    assert len(client.calls) == 1
    call = client.calls[0]
    assert call[0] == "commit_files"
    assert call[2] == "feature/404-thing"
    assert "Sub A" in call[3]
    assert "404" in call[3]
    assert call[4] == changed_files


def test_push_branch_delegates():
    client = FakeGithubClient()
    repo_path = Path("/repo")
    gw = GitWorkflow(repo_path, client, "backend")
    asyncio.run(gw.push_branch("feature/404-thing"))
    assert client.calls == [("push_branch", str(repo_path), "feature/404-thing")]


def test_open_pull_request_returns_url_from_client():
    client = FakeGithubClient()
    repo_path = Path("/repo")
    gw = GitWorkflow(repo_path, client, "backend")
    url = asyncio.run(gw.open_pull_request("feature/404-thing", "Title", "Body"))
    assert url == "https://github.com/org/repo/pull/1"
    assert client.calls == [("open_pull_request", str(repo_path), "feature/404-thing", "Title", "Body")]
