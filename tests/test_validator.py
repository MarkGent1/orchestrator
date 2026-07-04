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
        if isinstance(response, Exception):
            raise response
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


def test_fix_loop_illegal_path_from_attempt_fix_is_skipped_not_fatal(
    monkeypatch, tmp_path, backend_repo, model_config, patch_fix_loop
):
    """
    Regression test: FixLoop.attempt_fix() raises ValueError when the
    model proposes a path that violates Clean Architecture rules. This
    used to propagate out of run_validation() and crash the whole
    orchestrator process. It should now be treated as a failed attempt
    (logged, then retried) -- not fatal -- exactly like the equivalent
    fix already shipped for task_executor.py.
    """
    good_edits = [{"file": "src/UserModule/Foo.cs", "instructions": "modify", "content": "fixed"}]
    patch_fix_loop([ValueError("illegal path: src/NewModule/Foo.cs"), good_edits])

    build_runner = _make_runner([(False, "build broke"), (True, "build ok now")])
    monkeypatch.setattr(validator_module, "run_backend_build", build_runner)
    monkeypatch.setattr(validator_module, "run_backend_tests", _make_runner([(True, "tests ok")]))

    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=backend_repo, repo_type="backend",
        enforcer=CleanArchitectureEnforcer(backend_repo, "backend"), model_config=model_config,
        max_fix_attempts=3,
    )

    ok, message = asyncio.run(validator.run_validation())
    assert ok is True
    assert (backend_repo / "src" / "UserModule" / "Foo.cs").read_text() == "fixed"
    # First attempt raised and was skipped; second attempt succeeded.
    assert len(build_runner.calls) == 2


def test_fix_loop_illegal_path_from_apply_edits_is_skipped_not_fatal(
    monkeypatch, tmp_path, backend_repo, model_config, patch_fix_loop
):
    """
    Regression test: apply_file_edits_for_task() can also raise
    ValueError (e.g. a path that only becomes illegal after casing
    normalization). This must be contained the same way as an
    attempt_fix() failure -- skip the attempt, keep the run alive.
    """
    illegal_edits = [{"file": "src/NewModule/Foo.cs", "instructions": "modify", "content": "bad"}]
    good_edits = [{"file": "src/UserModule/Foo.cs", "instructions": "modify", "content": "fixed"}]
    patch_fix_loop([illegal_edits, good_edits])

    # The first attempt raises before ever calling the runner (it's
    # rejected by apply_file_edits_for_task()), so the runner is only
    # actually invoked twice: the initial build, then the retry after
    # the second (legal) attempt.
    build_runner = _make_runner([(False, "build broke"), (True, "build ok now")])
    monkeypatch.setattr(validator_module, "run_backend_build", build_runner)
    monkeypatch.setattr(validator_module, "run_backend_tests", _make_runner([(True, "tests ok")]))

    # FakeFixLoop bypasses FixLoop's own validation entirely, so the
    # illegal edit reaches apply_file_edits_for_task() unfiltered, and
    # that call's own enforcer check is what raises here.
    validator = BuildTestValidator(
        repo_path=tmp_path, temp_workspace=backend_repo, repo_type="backend",
        enforcer=CleanArchitectureEnforcer(backend_repo, "backend"), model_config=model_config,
        max_fix_attempts=3,
    )

    ok, message = asyncio.run(validator.run_validation())
    assert ok is True
    assert not (backend_repo / "src" / "NewModule").exists()
    assert (backend_repo / "src" / "UserModule" / "Foo.cs").read_text() == "fixed"


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
