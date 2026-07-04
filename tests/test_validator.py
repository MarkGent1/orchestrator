import asyncio

import pytest

import validator as validator_module
from validator import BuildTestValidator
from architecture.enforcement import CleanArchitectureEnforcer


class FakeFixLoop:
    """
    Replaces the real FixLoop (which would call an LLM). Each instance
    is told, up front, what to return on successive attempt_fix()
    calls -- e.g. [edits_for_attempt_1, edits_for_attempt_2, ...].
    """
    def __init__(self, *args, **kwargs):
        self.responses = list(FakeFixLoop.next_responses)
        self.calls = 0

    async def attempt_fix(self, error_output):
        response = self.responses[self.calls] if self.calls < len(self.responses) else []
        self.calls += 1
        return response


@pytest.fixture
def patch_fix_loop(monkeypatch):
    def _set(responses):
        FakeFixLoop.next_responses = responses
        monkeypatch.setattr(validator_module, "FixLoop", FakeFixLoop)
    return _set


def _make_runner(results):
    """results: list of (ok, output) tuples returned on successive calls."""
    calls = []

    def runner(workspace_path):
        idx = len(calls)
        calls.append(workspace_path)
        return results[idx] if idx < len(results) else results[-1]

    runner.calls = calls
    return runner


def test_backend_validation_passes_on_first_try(monkeypatch, tmp_path, backend_repo, model_config, patch_fix_loop):
    patch_fix_loop([])
    build_runner = _make_runner([(True, "build ok")])
    test_runner = _make_runner([(True, "tests ok")])
    monkeypatch.setattr(validator_module, "run_backend_build", build_runner)
    monkeypatch.setattr(validator_module, "run_backend_tests", test_runner)

    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=backend_repo, repo_type="backend",
        enforcer=CleanArchitectureEnforcer(backend_repo, "backend"), model_config=model_config,
    )

    ok, message = asyncio.run(validator.run_validation())
    assert ok is True
    assert message == "All validation steps passed"
    assert len(build_runner.calls) == 1
    assert len(test_runner.calls) == 1


def test_backend_build_fails_then_fix_loop_succeeds_on_retry(monkeypatch, tmp_path, backend_repo, model_config, patch_fix_loop):
    fix_edits = [{"file": "src/UserModule/Foo.cs", "instructions": "modify", "content": "fixed"}]
    patch_fix_loop([fix_edits])

    build_runner = _make_runner([(False, "build broke"), (True, "build ok now")])
    test_runner = _make_runner([(True, "tests ok")])
    monkeypatch.setattr(validator_module, "run_backend_build", build_runner)
    monkeypatch.setattr(validator_module, "run_backend_tests", test_runner)

    enforcer = CleanArchitectureEnforcer(backend_repo, "backend")
    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=backend_repo, repo_type="backend",
        enforcer=enforcer, model_config=model_config,
    )

    ok, message = asyncio.run(validator.run_validation())
    assert ok is True
    assert len(build_runner.calls) == 2  # initial failure + retry after fix
    assert (backend_repo / "src" / "UserModule" / "Foo.cs").read_text() == "fixed"


def test_fix_loop_returning_no_fix_stops_immediately(monkeypatch, tmp_path, backend_repo, model_config, patch_fix_loop):
    patch_fix_loop([[]])  # first attempt returns no possible fix

    build_runner = _make_runner([(False, "unfixable error")])
    monkeypatch.setattr(validator_module, "run_backend_build", build_runner)
    monkeypatch.setattr(validator_module, "run_backend_tests", _make_runner([(True, "n/a")]))

    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=backend_repo, repo_type="backend",
        enforcer=CleanArchitectureEnforcer(backend_repo, "backend"), model_config=model_config,
        max_fix_attempts=3,
    )

    ok, message = asyncio.run(validator.run_validation())
    assert ok is False
    assert "No fix possible" in message
    assert len(build_runner.calls) == 1  # never retried the build at all


def test_fix_loop_exhausted_after_max_attempts(monkeypatch, tmp_path, backend_repo, model_config, patch_fix_loop):
    edits = [{"file": "src/UserModule/Foo.cs", "instructions": "modify", "content": "still broken"}]
    patch_fix_loop([edits, edits])  # 2 attempts, both "fix" but build keeps failing

    build_runner = _make_runner([(False, "e1"), (False, "e2"), (False, "e3")])
    monkeypatch.setattr(validator_module, "run_backend_build", build_runner)
    monkeypatch.setattr(validator_module, "run_backend_tests", _make_runner([(True, "n/a")]))

    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=backend_repo, repo_type="backend",
        enforcer=CleanArchitectureEnforcer(backend_repo, "backend"), model_config=model_config,
        max_fix_attempts=2,
    )

    ok, message = asyncio.run(validator.run_validation())
    assert ok is False
    assert "Fix loop exhausted" in message
    assert len(build_runner.calls) == 3  # initial + 2 retries


def test_frontend_validation_runs_all_four_phases(monkeypatch, tmp_path, frontend_repo, model_config, patch_fix_loop):
    patch_fix_loop([])
    monkeypatch.setattr(validator_module, "run_frontend_build", _make_runner([(True, "ok")]))
    monkeypatch.setattr(validator_module, "run_frontend_tests", _make_runner([(True, "ok")]))
    monkeypatch.setattr(validator_module, "run_frontend_lint", _make_runner([(True, "ok")]))
    monkeypatch.setattr(validator_module, "run_frontend_format", _make_runner([(True, "ok")]))

    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=frontend_repo, repo_type="frontend", model_config=model_config,
    )
    ok, message = asyncio.run(validator.run_validation())
    assert ok is True


def test_fullstack_validation_runs_all_six_phases(monkeypatch, tmp_path, backend_repo, model_config, patch_fix_loop):
    patch_fix_loop([])
    for name in ("run_backend_build", "run_backend_tests", "run_frontend_build", "run_frontend_tests", "run_frontend_lint", "run_frontend_format"):
        monkeypatch.setattr(validator_module, name, _make_runner([(True, "ok")]))

    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=backend_repo, repo_type="fullstack", model_config=model_config,
    )
    ok, message = asyncio.run(validator.run_validation())
    assert ok is True


def test_unknown_repo_type_fails_immediately(tmp_path, backend_repo, model_config):
    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=backend_repo, repo_type="something-else", model_config=model_config,
    )
    ok, message = asyncio.run(validator.run_validation())
    assert ok is False
    assert "Unknown repo type" in message
