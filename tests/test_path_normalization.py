import pytest

from utils.path_normalization import normalize_path_casing


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "src" / "UserModule" / "Controllers").mkdir(parents=True)
    return tmp_path


@pytest.mark.parametrize(
    "raw_path,repo_type,expected",
    [
        ("new-feature/Controllers/Foo.cs", "backend", "NewFeature/Controllers/Foo.cs"),
        ("src/usermodule/controllers/Foo.cs", "backend", "src/UserModule/Controllers/Foo.cs"),
        ("src/UserModule/new-sub/deeper/File.cs", "backend", "src/UserModule/NewSub/Deeper/File.cs"),
        ("new-widgets/sub-thing/Foo.tsx", "frontend", "newWidgets/subThing/Foo.tsx"),
        ("controllers/Foo.cs", "backend", "Controllers/Foo.cs"),
    ],
)
def test_casing_rules_with_existing_workspace(workspace, raw_path, repo_type, expected):
    assert normalize_path_casing(raw_path, repo_type, workspace) == expected


@pytest.mark.parametrize(
    "raw_path,repo_type,expected",
    [
        # These are the exact corruption cases the _smart_segment_case
        # fix targets: str.capitalize() used to lowercase everything
        # after the first letter, destroying already-correct casing.
        ("RandomFolder/Foo.cs", "backend", "RandomFolder/Foo.cs"),
        ("NewFeatureModule/Foo.cs", "backend", "NewFeatureModule/Foo.cs"),
        ("newWidgets/Foo.tsx", "frontend", "newWidgets/Foo.tsx"),
        ("NewWidgets/Foo.tsx", "frontend", "newWidgets/Foo.tsx"),
        ("randomFolder/Foo.cs", "backend", "RandomFolder/Foo.cs"),
    ],
)
def test_preserves_or_corrects_casing_of_new_folders(workspace, raw_path, repo_type, expected):
    assert normalize_path_casing(raw_path, repo_type, workspace) == expected


def test_idempotent_on_second_application_backend(workspace):
    once = normalize_path_casing("new-feature-thing/Foo.cs", "backend", workspace)
    twice = normalize_path_casing(once, "backend", workspace)
    assert once == twice == "NewFeatureThing/Foo.cs"


def test_idempotent_on_second_application_frontend(workspace):
    once = normalize_path_casing("new-widget-thing/Foo.tsx", "frontend", workspace)
    twice = normalize_path_casing(once, "frontend", workspace)
    assert once == twice == "newWidgetThing/Foo.tsx"


def test_no_workspace_root_still_applies_casing():
    assert normalize_path_casing("new-thing/Foo.cs", "backend", None) == "NewThing/Foo.cs"


def test_does_not_crash_on_brand_new_multi_level_folder_no_workspace_root():
    """
    Regression test: current_path.iterdir() used to be called
    unconditionally, raising FileNotFoundError as soon as it walked
    into a folder segment that doesn't exist yet on disk. A two-level
    brand-new path (neither level exists) must not crash.
    """
    result = normalize_path_casing("BrandNew/StillNewer/File.cs", "backend", None)
    assert result == "BrandNew/StillNewer/File.cs"


def test_does_not_crash_on_brand_new_nested_folder_under_real_workspace(tmp_path):
    """Same crash, but with a real (mostly-empty) workspace_root supplied."""
    result = normalize_path_casing("TotallyNew/AlsoNew/File.cs", "backend", tmp_path)
    assert result == "TotallyNew/AlsoNew/File.cs"


def test_filenames_are_never_recased():
    result = normalize_path_casing("new-folder/lowercase_file_name.cs", "backend", None)
    assert result.endswith("/lowercase_file_name.cs")
