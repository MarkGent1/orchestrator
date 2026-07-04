import asyncio

import pytest

from fix_loop import FixLoop
from architecture.enforcement import CleanArchitectureEnforcer


def _enforcer(backend_repo):
    return CleanArchitectureEnforcer(backend_repo, "backend")


def test_attempt_fix_returns_edits_from_model(monkeypatch, backend_repo, model_config):
    fl = FixLoop(backend_repo, repo_type="backend", enforcer=_enforcer(backend_repo), model_config=model_config)

    async def fake_call_model(prompt, model, provider):
        return [{"file": "src/UserModule/Foo.cs", "instructions": "modify", "content": "fixed"}]

    monkeypatch.setattr("fix_loop.call_model", fake_call_model)

    edits = asyncio.run(fl.attempt_fix("some build error"))
    assert edits == [{"file": "src/UserModule/Foo.cs", "instructions": "modify", "content": "fixed"}]


def test_attempt_fix_raises_typeerror_when_model_returns_non_list(monkeypatch, backend_repo, model_config):
    fl = FixLoop(backend_repo, repo_type="backend", enforcer=_enforcer(backend_repo), model_config=model_config)

    async def fake_call_model(prompt, model, provider):
        return {"not": "a list"}

    monkeypatch.setattr("fix_loop.call_model", fake_call_model)

    with pytest.raises(TypeError):
        asyncio.run(fl.attempt_fix("error"))


def test_attempt_fix_raises_when_edit_missing_instructions(monkeypatch, backend_repo, model_config):
    fl = FixLoop(backend_repo, repo_type="backend", enforcer=_enforcer(backend_repo), model_config=model_config)

    async def fake_call_model(prompt, model, provider):
        return [{"file": "src/UserModule/Foo.cs", "content": "x"}]

    monkeypatch.setattr("fix_loop.call_model", fake_call_model)

    with pytest.raises(ValueError):
        asyncio.run(fl.attempt_fix("error"))


def test_attempt_fix_raises_when_edit_missing_file_path(monkeypatch, backend_repo, model_config):
    fl = FixLoop(backend_repo, repo_type="backend", enforcer=_enforcer(backend_repo), model_config=model_config)

    async def fake_call_model(prompt, model, provider):
        return [{"instructions": "modify", "content": "x"}]

    monkeypatch.setattr("fix_loop.call_model", fake_call_model)

    with pytest.raises(ValueError):
        asyncio.run(fl.attempt_fix("error"))


def test_attempt_fix_enforces_clean_architecture_path_rules(monkeypatch, backend_repo, model_config):
    """
    A fix targeting a brand-new top-level module (not inside an
    existing src/<Module>/ folder) must be rejected -- FixLoop should
    never be able to create new modules.
    """
    fl = FixLoop(backend_repo, repo_type="backend", enforcer=_enforcer(backend_repo), model_config=model_config)

    async def fake_call_model(prompt, model, provider):
        return [{"file": "src/BrandNewModule/Foo.cs", "instructions": "create", "content": "x"}]

    monkeypatch.setattr("fix_loop.call_model", fake_call_model)

    with pytest.raises(ValueError):
        asyncio.run(fl.attempt_fix("error"))


def test_attempt_fix_empty_list_is_a_valid_no_fix_response(monkeypatch, backend_repo, model_config):
    fl = FixLoop(backend_repo, repo_type="backend", enforcer=_enforcer(backend_repo), model_config=model_config)

    async def fake_call_model(prompt, model, provider):
        return []

    monkeypatch.setattr("fix_loop.call_model", fake_call_model)

    assert asyncio.run(fl.attempt_fix("error")) == []


def test_attempt_fix_selects_fixloop_model(monkeypatch, backend_repo, model_config):
    seen = {}

    async def fake_call_model(prompt, model, provider):
        seen["model"] = model
        seen["provider"] = provider
        return []

    monkeypatch.setattr("fix_loop.call_model", fake_call_model)

    fl = FixLoop(backend_repo, repo_type="backend", enforcer=_enforcer(backend_repo), model_config=model_config)
    asyncio.run(fl.attempt_fix("error"))

    assert seen["model"] == model_config["fixloop_model"]
