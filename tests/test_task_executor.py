import asyncio

import pytest

import task_executor
from task_executor import execute_subtask
from architecture.enforcement import CleanArchitectureEnforcer


async def _fake_prompt(**kwargs):
    return "fake prompt"


def test_execute_subtask_applies_edits_and_returns_changed_files(monkeypatch, backend_repo, model_config):
    monkeypatch.setattr(task_executor, "build_opencode_prompt_for_task", _fake_prompt)

    async def fake_call_model(prompt, model, provider):
        return [{"file": "src/UserModule/Foo.cs", "instructions": "create", "content": "// x"}]

    monkeypatch.setattr(task_executor, "call_model", fake_call_model)

    enforcer = CleanArchitectureEnforcer(backend_repo, "backend")
    changed = asyncio.run(execute_subtask(
        repo_path=backend_repo, workspace_path=backend_repo, work_item_id=404,
        work_item_title="Title", task={"title": "Task One"}, subtask={"title": "Sub A"},
        repo_type="backend", enforcer=enforcer, model_config=model_config,
    ))

    assert changed == [{"path": "src/UserModule/Foo.cs", "content": "// x"}]
    assert (backend_repo / "src" / "UserModule" / "Foo.cs").exists()


def test_execute_subtask_illegal_path_is_skipped_not_fatal(monkeypatch, backend_repo, model_config, capsys):
    """
    Regression test for a real production crash: the model proposed a
    brand-new test project directly under src/ (e.g.
    src/Something.Tests/Foo.cs), which Clean Architecture enforcement
    correctly rejects as an illegal new module. That ValueError used
    to propagate all the way out of execute_subtask() and crash the
    entire multi-task orchestrator run, discarding all subsequent
    tasks even though everything up to that point had already been
    committed successfully. It must now be caught, logged clearly, and
    treated like a subtask that produced no changes.
    """
    monkeypatch.setattr(task_executor, "build_opencode_prompt_for_task", _fake_prompt)

    async def fake_call_model(prompt, model, provider):
        return [{"file": "src/BrandNewModule.Tests/Foo.cs", "instructions": "create", "content": "// x"}]

    monkeypatch.setattr(task_executor, "call_model", fake_call_model)

    enforcer = CleanArchitectureEnforcer(backend_repo, "backend")
    changed = asyncio.run(execute_subtask(
        repo_path=backend_repo, workspace_path=backend_repo, work_item_id=404,
        work_item_title="Title", task={"title": "Task One"}, subtask={"title": "Add a test"},
        repo_type="backend", enforcer=enforcer, model_config=model_config,
    ))

    assert changed == []
    assert not (backend_repo / "src" / "BrandNewModule.Tests").exists()
    captured = capsys.readouterr()
    assert "invalid edit and was skipped" in captured.out


def test_execute_subtask_selects_model_by_subtask_title(monkeypatch, backend_repo, model_config):
    monkeypatch.setattr(task_executor, "build_opencode_prompt_for_task", _fake_prompt)
    seen = {}

    async def fake_call_model(prompt, model, provider):
        seen["model"] = model
        return []

    monkeypatch.setattr(task_executor, "call_model", fake_call_model)

    enforcer = CleanArchitectureEnforcer(backend_repo, "backend")
    asyncio.run(execute_subtask(
        repo_path=backend_repo, workspace_path=backend_repo, work_item_id=404,
        work_item_title="Title", task={"title": "Task One"}, subtask={"title": "Fix the bug"},
        repo_type="backend", enforcer=enforcer, model_config=model_config,
    ))

    assert seen["model"] == model_config["fixloop_model"]
