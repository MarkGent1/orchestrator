import asyncio

import pytest

import model_selector as ms


def test_resolve_provider_claude():
    assert ms.resolve_provider("claude-haiku-4-5") == ms.PROVIDER_CLAUDE


def test_resolve_provider_openai():
    assert ms.resolve_provider("gpt-5.4-mini") == ms.PROVIDER_OPENAI


def test_resolve_provider_unknown_raises():
    with pytest.raises(RuntimeError):
        ms.resolve_provider("llama-3")


def test_select_model_for_planning(model_config):
    model, provider = ms.select_model_for_planning(model_config)
    assert model == model_config["planning_model"]
    assert provider == ms.PROVIDER_CLAUDE


def test_select_model_for_decomposition(model_config):
    model, provider = ms.select_model_for_decomposition(model_config)
    assert model == model_config["decomposition_model"]
    assert provider == ms.PROVIDER_OPENAI


def test_select_model_for_fixloop(model_config):
    model, provider = ms.select_model_for_fixloop(model_config)
    assert model == model_config["fixloop_model"]
    assert provider == ms.PROVIDER_CLAUDE


@pytest.mark.parametrize("title", ["Fix broken build", "Repair failing test", "FIX the thing"])
def test_select_model_for_task_execution_routes_fix_titles_to_fixloop_model(model_config, title):
    model, provider = ms.select_model_for_task_execution(title, "backend", model_config)
    assert model == model_config["fixloop_model"]


def test_select_model_for_task_execution_routes_normal_titles_to_execution_model(model_config):
    model, provider = ms.select_model_for_task_execution("Implement UsersController", "backend", model_config)
    assert model == model_config["execution_model"]


def test_call_model_dispatches_to_claude_path(monkeypatch):
    calls = []

    async def fake_call_opencode(prompt, model=None):
        calls.append(("opencode", prompt, model))
        return "claude result"

    monkeypatch.setattr(ms, "call_opencode", fake_call_opencode)
    result = asyncio.run(ms.call_model("do it", "claude-haiku", ms.PROVIDER_CLAUDE))
    assert result == "claude result"
    assert calls == [("opencode", "do it", "claude-haiku")]


def test_call_model_dispatches_to_openai_path(monkeypatch):
    calls = []

    async def fake_call_openai(prompt, model=None):
        calls.append(("openai", prompt, model))
        return "gpt result"

    monkeypatch.setattr(ms, "call_openai", fake_call_openai)
    result = asyncio.run(ms.call_model("do it", "gpt-mini", ms.PROVIDER_OPENAI))
    assert result == "gpt result"
    assert calls == [("openai", "do it", "gpt-mini")]


def test_call_model_json_dispatches_by_provider(monkeypatch):
    async def fake_opencode_json(prompt, model=None):
        return {"from": "claude"}

    async def fake_openai_json(prompt, model=None):
        return {"from": "openai"}

    monkeypatch.setattr(ms, "call_opencode_json", fake_opencode_json)
    monkeypatch.setattr(ms, "call_openai_json", fake_openai_json)

    assert asyncio.run(ms.call_model_json("p", "claude-x", ms.PROVIDER_CLAUDE)) == {"from": "claude"}
    assert asyncio.run(ms.call_model_json("p", "gpt-x", ms.PROVIDER_OPENAI)) == {"from": "openai"}
