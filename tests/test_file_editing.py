import pytest

from file_editing import apply_file_edits_for_task


class AllowAllEnforcer:
    def validate_path(self, rel_path):
        return True


class BlockingEnforcer:
    def __init__(self, blocked):
        self.blocked = blocked

    def validate_path(self, rel_path):
        return rel_path not in self.blocked


def test_create_writes_file_and_returns_changed_entry(tmp_path):
    (tmp_path / "src").mkdir()  # pre-existing, as in a real checked-out repo
    edits = [{"path": "src/Foo.cs", "instructions": "create", "content": "hello"}]
    changed = apply_file_edits_for_task(tmp_path, edits, "backend")
    assert (tmp_path / "src" / "Foo.cs").read_text() == "hello"
    assert changed == [{"path": "src/Foo.cs", "content": "hello"}]


def test_modify_overwrites_existing_file(tmp_path):
    (tmp_path / "Foo.cs").write_text("old")
    edits = [{"path": "Foo.cs", "instructions": "modify", "content": "new"}]
    apply_file_edits_for_task(tmp_path, edits, "backend")
    assert (tmp_path / "Foo.cs").read_text() == "new"


def test_delete_removes_existing_file(tmp_path):
    (tmp_path / "Foo.cs").write_text("bye")
    edits = [{"path": "Foo.cs", "instructions": "delete", "content": None}]
    changed = apply_file_edits_for_task(tmp_path, edits, "backend")
    assert not (tmp_path / "Foo.cs").exists()
    assert changed == [{"path": "Foo.cs", "content": None}]


def test_delete_is_safe_when_file_does_not_exist(tmp_path):
    edits = [{"path": "Nope.cs", "instructions": "delete", "content": None}]
    changed = apply_file_edits_for_task(tmp_path, edits, "backend")
    assert changed == [{"path": "Nope.cs", "content": None}]


def test_accepts_alternate_path_key_names(tmp_path):
    for key in ("file", "file_path", "new_file", "filename"):
        edits = [{key: f"{key}.cs", "instructions": "create", "content": "x"}]
        apply_file_edits_for_task(tmp_path, edits, "backend")
        assert (tmp_path / f"{key}.cs").exists()


def test_raises_when_no_path_like_field(tmp_path):
    with pytest.raises(ValueError):
        apply_file_edits_for_task(tmp_path, [{"instructions": "create", "content": "x"}], "backend")


def test_raises_on_non_string_content(tmp_path):
    with pytest.raises(ValueError):
        apply_file_edits_for_task(
            tmp_path, [{"path": "Foo.cs", "instructions": "create", "content": 123}], "backend"
        )


def test_raises_on_unknown_instruction(tmp_path):
    with pytest.raises(ValueError):
        apply_file_edits_for_task(
            tmp_path, [{"path": "Foo.cs", "instructions": "rename", "content": "x"}], "backend"
        )


def test_enforcer_blocks_illegal_raw_path(tmp_path):
    enforcer = BlockingEnforcer(blocked={"escape/../Foo.cs"})
    with pytest.raises(ValueError):
        apply_file_edits_for_task(
            tmp_path,
            [{"path": "escape/../Foo.cs", "instructions": "create", "content": "x"}],
            "backend",
            enforcer=enforcer,
        )


def test_enforcer_allows_when_path_permitted(tmp_path):
    (tmp_path / "src" / "Module").mkdir(parents=True)  # pre-existing module
    enforcer = AllowAllEnforcer()
    changed = apply_file_edits_for_task(
        tmp_path,
        [{"path": "src/Module/Foo.cs", "instructions": "create", "content": "x"}],
        "backend",
        enforcer=enforcer,
    )
    assert changed[0]["path"] == "src/Module/Foo.cs"


def test_no_enforcer_skips_path_validation_entirely(tmp_path):
    (tmp_path / "src").mkdir()
    # Should not raise even though there's no enforcer to consult.
    changed = apply_file_edits_for_task(
        tmp_path,
        [{"path": "src/Anything/Foo.cs", "instructions": "create", "content": "x"}],
        "backend",
        enforcer=None,
    )
    assert changed[0]["path"] == "src/Anything/Foo.cs"


def test_multiple_edits_processed_in_order(tmp_path):
    edits = [
        {"path": "a.cs", "instructions": "create", "content": "1"},
        {"path": "b.cs", "instructions": "create", "content": "2"},
    ]
    changed = apply_file_edits_for_task(tmp_path, edits, "backend")
    assert [c["path"] for c in changed] == ["a.cs", "b.cs"]
