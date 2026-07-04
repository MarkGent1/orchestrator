import json
import pytest

import run_state as run_state_module
from run_state import RunState


@pytest.fixture(autouse=True)
def isolated_state_dir(tmp_path, monkeypatch):
    """
    Point RunState's module-level STATE_DIR at a throwaway directory
    for every test, so tests never touch the real
    .orchestrator-state/ folder and never see state left over from a
    previous test.
    """
    state_dir = tmp_path / ".orchestrator-state"
    monkeypatch.setattr(run_state_module, "STATE_DIR", state_dir)
    return state_dir


@pytest.fixture
def repo_path(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


def test_load_returns_none_when_no_state_file(repo_path):
    assert RunState.load(repo_path, 404) is None


def test_init_plan_persists_and_reloads(repo_path):
    state = RunState(repo_path, 404)
    tasks = [
        {"title": "Task One", "description": "d1"},
        {"title": "Task Two", "description": "d2"},
    ]
    state.init_plan("feature/404-add-thing", "Add Thing", tasks)

    reloaded = RunState.load(repo_path, 404)
    assert reloaded is not None
    assert reloaded.branch_name == "feature/404-add-thing"
    assert reloaded.plan_title == "Add Thing"
    assert [t["title"] for t in reloaded.tasks] == ["Task One", "Task Two"]
    assert all(t["done"] is False for t in reloaded.tasks)


def test_set_task_subtasks_and_is_subtask_done(repo_path):
    state = RunState(repo_path, 404)
    state.init_plan("branch", "Title", [{"title": "Task One", "description": ""}])
    state.set_task_subtasks("Task One", [{"title": "Sub A", "description": ""}, {"title": "Sub B", "description": ""}])

    assert state.is_subtask_done("Task One", "Sub A") is False
    assert state.is_subtask_done("Task One", "Sub B") is False


def test_mark_subtask_done_persists_and_marks_task_done_when_all_complete(repo_path):
    state = RunState(repo_path, 404)
    state.init_plan("branch", "Title", [{"title": "Task One", "description": ""}])
    state.set_task_subtasks("Task One", [{"title": "Sub A", "description": ""}, {"title": "Sub B", "description": ""}])

    state.mark_subtask_done("Task One", "Sub A")
    reloaded = RunState.load(repo_path, 404)
    assert reloaded.is_subtask_done("Task One", "Sub A") is True
    assert reloaded.is_subtask_done("Task One", "Sub B") is False
    assert reloaded.get_task("Task One")["done"] is False

    reloaded.mark_subtask_done("Task One", "Sub B")
    reloaded2 = RunState.load(repo_path, 404)
    assert reloaded2.get_task("Task One")["done"] is True


def test_get_task_returns_none_for_unknown_title(repo_path):
    state = RunState(repo_path, 404)
    state.init_plan("branch", "Title", [{"title": "Task One", "description": ""}])
    assert state.get_task("Nonexistent") is None


def test_mark_validated_and_mark_pr_opened_persist(repo_path):
    state = RunState(repo_path, 404)
    state.init_plan("branch", "Title", [{"title": "Task One", "description": ""}])
    state.mark_validated()
    state.mark_pr_opened("https://github.com/org/repo/pull/1")

    reloaded = RunState.load(repo_path, 404)
    assert reloaded.validated is True
    assert reloaded.pr_url == "https://github.com/org/repo/pull/1"


def test_clear_removes_state_file(repo_path):
    state = RunState(repo_path, 404)
    state.init_plan("branch", "Title", [{"title": "Task One", "description": ""}])
    assert state.path.exists()

    state.clear()
    assert not state.path.exists()
    assert RunState.load(repo_path, 404) is None


def test_clear_is_safe_when_no_state_file_exists(repo_path):
    state = RunState(repo_path, 404)
    state.clear()  # must not raise


def test_corrupt_state_file_fails_open_instead_of_crashing(repo_path, isolated_state_dir):
    state = RunState(repo_path, 404)
    state.init_plan("branch", "Title", [{"title": "Task One", "description": ""}])
    state.path.write_text("{ not valid json ]", encoding="utf-8")

    assert RunState.load(repo_path, 404) is None


def test_different_repos_never_collide(tmp_path):
    repo_a = tmp_path / "repo_a"
    repo_b = tmp_path / "repo_b"
    repo_a.mkdir()
    repo_b.mkdir()

    state_a = RunState(repo_a, 404)
    state_a.init_plan("branch-a", "Title A", [{"title": "T", "description": ""}])

    assert RunState.load(repo_b, 404) is None
    assert RunState.load(repo_a, 404) is not None


def test_different_work_item_ids_on_same_repo_never_collide(repo_path):
    state_1 = RunState(repo_path, 404)
    state_1.init_plan("branch-404", "Title 404", [{"title": "T", "description": ""}])

    state_2 = RunState(repo_path, 405)
    assert RunState.load(repo_path, 405) is None
    assert RunState.load(repo_path, 404) is not None


def test_save_is_atomic_no_leftover_tmp_file(repo_path):
    state = RunState(repo_path, 404)
    state.init_plan("branch", "Title", [{"title": "Task One", "description": ""}])
    tmp_file = state.path.with_suffix(".json.tmp")
    assert not tmp_file.exists()
    assert json.loads(state.path.read_text())["branch_name"] == "branch"
