from pr_enhancer import build_pr_description
from task_memory import TaskMemory


def _plan():
    return {
        "id": 404,
        "title": "Add UsersController",
        "repo_type": "backend",
        "tasks": [
            {"title": "Task One", "description": "d1"},
            {"title": "Task Two", "description": "d2"},
        ],
    }


def test_categorizes_implemented_test_and_other_subtasks():
    tm = TaskMemory()
    tm.add("Task One", "Implement UsersController", [], notes="")
    tm.add("Task One", "Add unit tests for UsersController", [], notes="")
    tm.add("Task Two", "Refactor service layer", [], notes="")

    body = build_pr_description(_plan(), tm, "all good")

    assert "### Implemented" in body
    assert "Implement UsersController" in body
    assert "### Tests Added" in body
    assert "Add unit tests for UsersController" in body
    assert "### Additional Work" in body
    assert "Refactor service layer" in body


def test_includes_work_item_title_and_id():
    tm = TaskMemory()
    body = build_pr_description(_plan(), tm, "all good")
    assert "Work Item 404" in body
    assert "Add UsersController" in body


def test_includes_repo_type_and_build_logs():
    tm = TaskMemory()
    body = build_pr_description(_plan(), tm, "build output here")
    assert "backend changes" in body
    assert "build output here" in body


def test_defaults_repo_type_to_backend_when_missing():
    plan = _plan()
    del plan["repo_type"]
    tm = TaskMemory()
    body = build_pr_description(plan, tm, "ok")
    assert "backend changes" in body


def test_omits_empty_sections():
    tm = TaskMemory()  # no entries at all
    body = build_pr_description(_plan(), tm, "ok")
    assert "### Implemented" not in body
    assert "### Tests Added" not in body
    assert "### Additional Work" not in body
