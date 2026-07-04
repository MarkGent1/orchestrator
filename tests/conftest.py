import sys
from pathlib import Path

# Make project-root modules (work_item_planning, run_state, utils.*, etc.)
# importable regardless of pytest's rootdir/import-mode detection, since
# tests/ has no __init__.py and sits one level below the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Some modules (model_selector -> opencode_client/openai_client) import
# the real anthropic/openai SDKs and call dotenv.load_dotenv() at
# import time. None of these tests make real network calls -- they
# mock at the call_model/call_model_json layer -- but the imports
# still need to succeed. If a real environment already has these
# packages installed (as the project's own venv does), this is a
# complete no-op and the real packages are used untouched; it only
# installs a lightweight stand-in when the real package genuinely
# isn't available (e.g. a minimal CI/test-only environment).
import types


def _stub_missing_module(name, **attrs):
    try:
        __import__(name)
    except ImportError:
        mod = types.ModuleType(name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        sys.modules[name] = mod


_stub_missing_module("dotenv", load_dotenv=lambda *a, **k: None)
_stub_missing_module("anthropic", AsyncAnthropic=object)
_stub_missing_module("openai", AsyncOpenAI=object)

import pytest


@pytest.fixture
def backend_repo(tmp_path):
    """
    A minimal backend repo: one .sln at the root and one module
    (UserModule) under src/ with a .csproj, plus an empty tests/ dir.
    Mirrors the shape CleanArchitectureEnforcer / repo_type / preflight
    expect for a real C#/.NET repo.
    """
    (tmp_path / "src" / "UserModule").mkdir(parents=True)
    (tmp_path / "src" / "UserModule" / "UserModule.csproj").write_text("<Project />")
    (tmp_path / "tests").mkdir()
    (tmp_path / "Solution.sln").write_text("Microsoft Visual Studio Solution File")
    return tmp_path


@pytest.fixture
def frontend_repo(tmp_path):
    """A minimal frontend repo: package.json at the root."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "package.json").write_text('{"name": "app", "version": "1.0.0"}')
    return tmp_path


@pytest.fixture
def model_config():
    """
    Fake model routing config. Values only need to start with
    "claude"/"gpt" so model_selector.resolve_provider() can route them;
    tests mock the actual call_model/call_model_json layer so no real
    API calls are ever made.
    """
    return {
        "planning_model": "claude-planning-test",
        "decomposition_model": "gpt-decomposition-test",
        "execution_model": "claude-execution-test",
        "fixloop_model": "claude-fixloop-test",
    }
