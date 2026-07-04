from utils.path_unifier import unify_path


def test_converts_windows_slashes():
    assert unify_path("src\\Module\\Foo.cs") == "src/Module/Foo.cs"


def test_strips_leading_dot_slash():
    assert unify_path("./src/Foo.cs") == "src/Foo.cs"


def test_collapses_duplicate_slashes():
    assert unify_path("src//Module///Foo.cs") == "src/Module/Foo.cs"


def test_strips_surrounding_whitespace():
    assert unify_path("  src/Foo.cs  ") == "src/Foo.cs"


def test_empty_input_returns_empty_string():
    assert unify_path("") == ""


def test_already_clean_path_is_unchanged():
    assert unify_path("src/Module/Foo.cs") == "src/Module/Foo.cs"
