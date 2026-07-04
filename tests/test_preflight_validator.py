from unittest.mock import patch, MagicMock

import preflight_validator as pv


def _fake_popen(returncode, output=""):
    proc = MagicMock()
    proc.communicate.return_value = (output, None)
    proc.returncode = returncode
    return proc


def test_detect_backend_finds_sln(tmp_path):
    (tmp_path / "App.sln").write_text("x")
    assert pv.detect_backend(tmp_path) == tmp_path / "App.sln"


def test_detect_backend_none_when_absent(tmp_path):
    assert pv.detect_backend(tmp_path) is None


def test_detect_frontend_root_only(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    assert pv.detect_frontend(tmp_path) == tmp_path


def test_detect_frontend_ignores_nested_frontend_folder(tmp_path):
    """
    Repos never have a "frontend/" subfolder convention -- only a
    root-level package.json counts.
    """
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package.json").write_text("{}")
    assert pv.detect_frontend(tmp_path) is None


def test_preflight_fails_when_neither_backend_nor_frontend_detected(tmp_path):
    ok, message = pv.preflight_validate(tmp_path)
    assert ok is False
    assert "Could not detect" in message


def test_preflight_backend_only_success(tmp_path):
    (tmp_path / "App.sln").write_text("x")
    with patch.object(pv.subprocess, "Popen", return_value=_fake_popen(0, "ok")):
        ok, message = pv.preflight_validate(tmp_path)
    assert ok is True
    assert "Backend pre-flight passed" in message


def test_preflight_backend_only_failure_surfaces_output(tmp_path):
    (tmp_path / "App.sln").write_text("x")
    with patch.object(pv.subprocess, "Popen", return_value=_fake_popen(1, "build broke")):
        ok, message = pv.preflight_validate(tmp_path)
    assert ok is False
    assert "build broke" in message


def test_preflight_frontend_only_success(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    with patch.object(pv.subprocess, "Popen", return_value=_fake_popen(0, "ok")):
        ok, message = pv.preflight_validate(tmp_path)
    assert ok is True
    assert "Frontend pre-flight passed" in message


def test_preflight_fullstack_runs_both_and_succeeds(tmp_path):
    (tmp_path / "App.sln").write_text("x")
    (tmp_path / "package.json").write_text("{}")
    with patch.object(pv.subprocess, "Popen", return_value=_fake_popen(0, "ok")):
        ok, message = pv.preflight_validate(tmp_path)
    assert ok is True
    assert "fullstack" in message


def test_preflight_fullstack_stops_at_first_failure(tmp_path):
    """Backend fails -> frontend validation must not run at all."""
    (tmp_path / "App.sln").write_text("x")
    (tmp_path / "package.json").write_text("{}")
    with patch.object(pv.subprocess, "Popen", return_value=_fake_popen(1, "backend broke")) as popen:
        ok, message = pv.preflight_validate(tmp_path)
    assert ok is False
    assert "backend broke" in message
    # Only the restore call should have run before bailing out.
    assert popen.call_count == 1
