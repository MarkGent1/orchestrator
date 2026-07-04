import asyncio

import pytest

import prompt_builder
from prompt_builder import build_opencode_prompt_for_task, collect_relevant_files
from architecture.enforcement import CleanArchitectureEnforcer


def _build_backend_repo_with_tests(tmp_path):
    (tmp_path / "src" / "UserModule" / "Controllers").mkdir(parents=True)
    (tmp_path / "src" / "UserModule" / "UserModule.csproj").write_text("<Project />")
    (tmp_path / "src" / "UserModule" / "Controllers" / "UsersController.cs").write_text(
        "namespace UserModule.Controllers; public class UsersController {}"
    )
    (tmp_path / "tests" / "UserModule.Unit.Tests" / "Controllers").mkdir(parents=True)
    (tmp_path / "tests" / "UserModule.Unit.Tests" / "UserModule.Unit.Tests.csproj").write_text("<Project />")
    (tmp_path / "tests" / "UserModule.Unit.Tests" / "Controllers" / "UsersControllerTests.cs").write_text(
        "namespace UserModule.Unit.Tests.Controllers; public class UsersControllerTests {}"
    )
    return tmp_path


def test_repo_tree_includes_existing_test_projects(tmp_path):
    """
    Regression test: the repo tree shown to the model previously
    excluded tests/ entirely (it shared EXCLUDED_DIRS with
    collect_relevant_files), so the model had no way to see that a
    test project like UserModule.Unit.Tests/ already existed. Asked to
    add a unit test, it would invent a brand new test project under
    src/ instead, which Clean Architecture enforcement then rejected,
    crashing the whole run. The tree must show tests/ paths even
    though their file *content* is still kept out of the prompt.
    """
    repo = _build_backend_repo_with_tests(tmp_path)
    enforcer = CleanArchitectureEnforcer(repo, "backend")

    prompt = asyncio.run(build_opencode_prompt_for_task(
        repo_path=repo,
        work_item_id=1,
        work_item_title="Add a feature",
        task={"title": "Add a test", "description": ""},
        repo_type="backend",
        enforcer=enforcer,
    ))

    assert "tests/UserModule.Unit.Tests" in prompt
    assert "UsersControllerTests.cs" in prompt


def test_relevant_files_still_exclude_test_file_content(tmp_path):
    """
    The tree fix must not also start dumping full test file *content*
    into the prompt -- collect_relevant_files() (a separate exclusion
    list) still prunes tests/ to keep prompt size down.
    """
    repo = _build_backend_repo_with_tests(tmp_path)
    relevant = collect_relevant_files(repo, "backend")
    assert not any("tests/" in f["path"] for f in relevant)


def test_prompt_includes_test_placement_rules_for_backend(tmp_path):
    repo = _build_backend_repo_with_tests(tmp_path)
    enforcer = CleanArchitectureEnforcer(repo, "backend")

    prompt = asyncio.run(build_opencode_prompt_for_task(
        repo_path=repo,
        work_item_id=1,
        work_item_title="Add a feature",
        task={"title": "Add a test", "description": ""},
        repo_type="backend",
        enforcer=enforcer,
    ))

    assert "Test Placement Rules" in prompt
    assert "MUST NOT create a new test project" in prompt


def test_prompt_includes_test_placement_rules_for_frontend(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "package.json").write_text("{}")

    prompt = asyncio.run(build_opencode_prompt_for_task(
        repo_path=tmp_path,
        work_item_id=1,
        work_item_title="Add a feature",
        task={"title": "Add a test", "description": ""},
        repo_type="frontend",
        enforcer=None,
    ))

    assert "Test Placement Rules" in prompt


def test_raises_when_backend_repo_missing_enforcer(tmp_path):
    with pytest.raises(ValueError):
        asyncio.run(build_opencode_prompt_for_task(
            repo_path=tmp_path,
            work_item_id=1,
            work_item_title="Add a feature",
            task={"title": "Add a test", "description": ""},
            repo_type="backend",
            enforcer=None,
        ))
