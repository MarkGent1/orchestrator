from repo_type import detect_repo_type


def test_detects_backend_via_sln(tmp_path):
    (tmp_path / "Solution.sln").write_text("x")
    assert detect_repo_type(tmp_path) == "backend"


def test_detects_backend_via_slnx(tmp_path):
    (tmp_path / "Solution.slnx").write_text("x")
    assert detect_repo_type(tmp_path) == "backend"


def test_detects_backend_via_nested_csproj_only(tmp_path):
    (tmp_path / "src" / "Module").mkdir(parents=True)
    (tmp_path / "src" / "Module" / "Module.csproj").write_text("x")
    assert detect_repo_type(tmp_path) == "backend"


def test_detects_frontend_via_root_package_json(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    assert detect_repo_type(tmp_path) == "frontend"


def test_detects_fullstack_when_both_signals_present(tmp_path):
    (tmp_path / "Solution.sln").write_text("x")
    (tmp_path / "package.json").write_text("{}")
    assert detect_repo_type(tmp_path) == "fullstack"


def test_unknown_when_neither_signal_present(tmp_path):
    (tmp_path / "readme.md").write_text("x")
    assert detect_repo_type(tmp_path) == "unknown"


def test_no_frontend_subfolder_convention_supported(tmp_path):
    """
    Repos are single-type with src/ and tests/ at the root -- a
    package.json living inside a nested "frontend/" folder (old
    monorepo-style convention) must NOT trigger frontend detection,
    since that folder convention doesn't exist in this project's repos
    and previously risked misclassifying an unrelated nested
    package.json as a real frontend.
    """
    (tmp_path / "src" / "Module").mkdir(parents=True)
    (tmp_path / "src" / "Module" / "Module.csproj").write_text("x")
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "package.json").write_text("{}")
    assert detect_repo_type(tmp_path) == "backend"
