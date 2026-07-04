import subprocess
import shutil
from pathlib import Path

import pytest

import main as main_module
import repo_type as repo_type_module
import run_state as run_state_module


def _run_git(args, cwd):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r.stdout.strip()


def _setup_repo(repo):
    repo.mkdir(parents=True, exist_ok=True)
    _run_git(["init", "-q"], repo)
    _run_git(["config", "user.email", "test@test.com"], repo)
    _run_git(["config", "user.name", "Test"], repo)
    (repo / "src" / "TestModule").mkdir(parents=True)
    (repo / "src" / "TestModule" / "TestModule.csproj").write_text("")
    (repo / "tests").mkdir()
    (repo / "Test.sln").write_text("sln")
    _run_git(["add", "-A"], repo)
    _run_git(["commit", "-q", "-m", "initial commit"], repo)


class FakeAdoMcpClient:
    def __init__(self, server_path):
        pass

    def close(self):
        pass

    async def link_pr(self, work_item_id, pr_url):
        pass


class FakeGithubMcpClient:
    """Performs REAL git operations so the test can verify actual repo state."""

    def __init__(self, server_path):
        pass

    def close(self):
        pass

    async def create_branch(self, repo_path, branch_name):
        existing = subprocess.run(["git", "rev-parse", "--verify", branch_name],
                                   cwd=repo_path, capture_output=True, text=True)
        if existing.returncode == 0:
            _run_git(["checkout", branch_name], repo_path)
        else:
            _run_git(["checkout", "-b", branch_name], repo_path)

    async def commit_files(self, repo_path, branch_name, message, files):
        _run_git(["checkout", branch_name], repo_path)
        for f in files:
            full = Path(repo_path) / f["path"]
            full.parent.mkdir(parents=True, exist_ok=True)
            if f["content"] is None:
                if full.exists():
                    full.unlink()
            else:
                full.write_text(f["content"])
        _run_git(["add", "-A"], repo_path)
        _run_git(["commit", "-q", "-m", message], repo_path)

    async def push_branch(self, repo_path, branch_name):
        pass

    async def open_pull_request(self, repo_path, branch_name, title, body):
        return "https://github.com/fake/repo/pull/1"


class FakeWorkItemPlanner:
    def __init__(self, ado, model_config):
        pass

    async def plan_work_item(self, work_item_id):
        FakeWorkItemPlanner.call_count += 1
        return {
            "plan": {
                "title": "Add UsersController",
                "tasks": [
                    {"title": "Task One", "description": "d1"},
                    {"title": "Task Two", "description": "d2"},
                ],
            },
            "created_tasks": [],
            "quality_issues": [],
        }


class FakeEnforcer:
    def __init__(self, *a, **k):
        pass

    def describe_modules(self):
        return "(fake modules)"

    def validate_path(self, p):
        return True


class FakeValidator:
    def __init__(self, **kwargs):
        pass

    async def run_validation(self):
        return True, "all good"


@pytest.fixture
def resume_harness(tmp_path, monkeypatch):
    """
    Wires main.py up to fakes for every external collaborator (ADO,
    GitHub, the planning/decomposition/execution model calls,
    preflight, and repo-type detection) so main.main() can be run
    end-to-end against a real (throwaway) git repo without any real
    network access, LLM calls, dotnet/npm, or Node MCP servers.
    """
    repo = tmp_path / "repo"
    _setup_repo(repo)

    state_dir = tmp_path / ".orchestrator-state"
    monkeypatch.setattr(run_state_module, "STATE_DIR", state_dir)

    FakeWorkItemPlanner.call_count = 0
    decompose_calls = []
    execute_calls = []
    crash_state = {"enabled": True}

    async def fake_decompose_task(work_item_id, plan_title, task, repo_type, model_config):
        decompose_calls.append(task["title"])
        return [
            {"title": f"{task['title']} - Sub A", "description": "sub a"},
            {"title": f"{task['title']} - Sub B", "description": "sub b"},
        ]

    async def fake_execute_subtask(repo_path, workspace_path, work_item_id, work_item_title,
                                    task, subtask, repo_type, enforcer, model_config):
        execute_calls.append(subtask["title"])
        if (crash_state["enabled"]
                and task["title"] == "Task Two"
                and subtask["title"] == "Task Two - Sub B"):
            raise RuntimeError("Simulated crash: model call failed")
        filename = subtask["title"].replace(" ", "_") + ".cs"
        return [{"path": f"src/TestModule/{filename}", "content": f"// {subtask['title']}"}]

    monkeypatch.setattr(main_module, "AdoMcpClient", FakeAdoMcpClient)
    monkeypatch.setattr(main_module, "GithubMcpClient", FakeGithubMcpClient)
    monkeypatch.setattr(main_module, "WorkItemPlanner", FakeWorkItemPlanner)
    monkeypatch.setattr(main_module, "decompose_task", fake_decompose_task)
    monkeypatch.setattr(main_module, "execute_subtask", fake_execute_subtask)
    monkeypatch.setattr(main_module, "BuildTestValidator", FakeValidator)
    monkeypatch.setattr(main_module, "build_pr_description", lambda plan, task_memory, message: "PR BODY")
    monkeypatch.setattr(main_module, "preflight_validate", lambda p: (True, "preflight ok"))
    monkeypatch.setattr(main_module, "build_module_map", lambda root: {})
    monkeypatch.setattr(main_module, "print_tree", lambda *a, **k: None)
    monkeypatch.setattr(main_module, "copy_repo_to_workspace", lambda src, dst: None)
    monkeypatch.setattr(main_module, "CleanArchitectureEnforcer", FakeEnforcer)
    monkeypatch.setattr(repo_type_module, "detect_repo_type", lambda p: "backend")

    return {
        "repo": repo,
        "decompose_calls": decompose_calls,
        "execute_calls": execute_calls,
        "crash_state": crash_state,
    }


async def _run_main(argv, monkeypatch):
    monkeypatch.setattr("sys.argv", argv)
    await main_module.main()


def test_crash_then_resume_completes_full_run(resume_harness, monkeypatch):
    import asyncio

    repo = resume_harness["repo"]
    decompose_calls = resume_harness["decompose_calls"]
    execute_calls = resume_harness["execute_calls"]
    crash_state = resume_harness["crash_state"]

    argv = ["main.py", "404", "--repo", str(repo)]

    # ---- RUN 1: expect a crash partway through Task Two ----
    with pytest.raises(RuntimeError, match="Simulated crash"):
        asyncio.run(_run_main(argv, monkeypatch))

    assert FakeWorkItemPlanner.call_count == 1
    assert decompose_calls == ["Task One", "Task Two"]
    assert execute_calls == ["Task One - Sub A", "Task One - Sub B", "Task Two - Sub A", "Task Two - Sub B"]

    state = run_state_module.RunState.load(repo, 404)
    assert state is not None
    assert state.get_task("Task One")["done"] is True
    assert state.get_task("Task Two")["done"] is False
    assert state.is_subtask_done("Task Two", "Task Two - Sub A") is True
    assert state.is_subtask_done("Task Two", "Task Two - Sub B") is False

    branch_name = state.branch_name
    assert branch_name in _run_git(["branch"], repo)

    log = _run_git(["log", "--oneline", branch_name], repo)
    assert len(log.splitlines()) == 1 + 3  # initial commit + 3 subtask commits

    # Simulate the user closing the terminal and coming back later on
    # the base branch, as a real repo would sit between runs.
    _run_git(["checkout", "master"], repo)
    assert _run_git(["branch", "--show-current"], repo) == "master"

    # ---- RUN 2: "fix the bug" (disable the crash) and resume ----
    decompose_calls.clear()
    execute_calls.clear()
    FakeWorkItemPlanner.call_count = 0
    crash_state["enabled"] = False

    asyncio.run(_run_main(argv, monkeypatch))

    assert FakeWorkItemPlanner.call_count == 0  # did not replan via AI
    assert "Task One" not in decompose_calls  # did not redecompose completed tasks
    assert "Task Two" not in decompose_calls
    assert execute_calls == ["Task Two - Sub B"]  # only the missing subtask ran

    final_log = _run_git(["log", "--oneline", branch_name], repo)
    assert len(final_log.splitlines()) == 1 + 4  # initial + 3 (run 1) + 1 (run 2)

    assert run_state_module.RunState.load(repo, 404) is None  # cleared after full completion
