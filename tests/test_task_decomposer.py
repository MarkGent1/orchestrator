import asyncio

from task_decomposer import decompose_task


def test_decompose_task_returns_subtasks_from_model(monkeypatch, model_config):
    async def fake_call_model_json(prompt, model, provider):
        return [{"title": "Sub A", "description": "d1"}]

    monkeypatch.setattr("task_decomposer.call_model_json", fake_call_model_json)

    result = asyncio.run(decompose_task(404, "Add UsersController", {"title": "Task One", "description": "d"}, "backend", model_config))
    assert result == [{"title": "Sub A", "description": "d1"}]


def test_decompose_task_defensively_returns_empty_list_for_non_list_model_output(monkeypatch, model_config):
    """
    Unlike WorkItemPlanner (which raises ValueError on bad model
    output), decompose_task intentionally fails soft here and returns
    [] so a single malformed decomposition doesn't crash the whole run.
    """
    async def fake_call_model_json(prompt, model, provider):
        return {"not": "a list"}

    monkeypatch.setattr("task_decomposer.call_model_json", fake_call_model_json)

    result = asyncio.run(decompose_task(404, "Title", {"title": "Task One", "description": "d"}, "backend", model_config))
    assert result == []


def test_decompose_task_selects_decomposition_model(monkeypatch, model_config):
    seen = {}

    async def fake_call_model_json(prompt, model, provider):
        seen["model"] = model
        return []

    monkeypatch.setattr("task_decomposer.call_model_json", fake_call_model_json)
    asyncio.run(decompose_task(404, "Title", {"title": "Task One", "description": "d"}, "backend", model_config))
    assert seen["model"] == model_config["decomposition_model"]
