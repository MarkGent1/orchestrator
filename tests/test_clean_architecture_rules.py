import pytest
from architecture.enforcement import CleanArchitectureEnforcer


@pytest.fixture
def enforcer(tmp_path):
    # Simulate a repo with one module
    (tmp_path / "src" / "UserModule").mkdir(parents=True)
    (tmp_path / "src" / "UserModule" / "UserModule.csproj").write_text("")

    # Simulate tests folder
    (tmp_path / "tests").mkdir()

    return CleanArchitectureEnforcer(tmp_path, repo_type="backend")


# ---------------------------------------------------------
# Allowed paths
# ---------------------------------------------------------

@pytest.mark.parametrize("path", [
    "src/UserModule/Controllers/UserController.cs",
    "src/UserModule/Database/Setup/Init.cs",
    "src/UserModule/Anything/Deep/Nested/File.cs",
])
def test_allows_paths_inside_module(enforcer, path):
    assert enforcer.validate_path(path)


@pytest.mark.parametrize("path", [
    "Program.cs",
    "Mav.UserMgmt.slnx",
    "docker-compose.yml",
])
def test_allows_root_level_files(enforcer, path):
    assert enforcer.validate_path(path)


@pytest.mark.parametrize("path", [
    "tests/UserModule.Tests/SomeTest.cs",
    "tests/Integration/HealthCheckTests.cs",
])
def test_allows_tests(enforcer, path):
    assert enforcer.validate_path(path)


# ---------------------------------------------------------
# Blocked paths
# ---------------------------------------------------------

@pytest.mark.parametrize("path", [
    "src/NewModule/Controllers/Test.cs",
])
def test_blocks_new_modules(enforcer, path):
    assert not enforcer.validate_path(path)


@pytest.mark.parametrize("path", [
    "RandomFolder/File.cs",
    "scripts/build.ps1",
    "docs/readme.md",
])
def test_blocks_outside_src_and_tests(enforcer, path):
    assert not enforcer.validate_path(path)


@pytest.mark.parametrize("path", [
    "Models/User.cs",
    "Controllers/UserController.cs",
])
def test_blocks_invalid_top_level(enforcer, path):
    assert not enforcer.validate_path(path)
