from task_memory import TaskMemory


def test_add_appends_entry():
    tm = TaskMemory()
    tm.add("Task One", "Sub A", [{"path": "a.cs", "content": "x"}], notes="done")
    assert tm.entries == [{
        "task": "Task One",
        "subtask": "Sub A",
        "changed_files": [{"path": "a.cs", "content": "x"}],
        "notes": "done",
    }]


def test_to_markdown_lists_tasks_and_files():
    tm = TaskMemory()
    tm.add("Task One", "Sub A", [{"path": "a.cs", "content": "x"}], notes="")
    tm.add("Task One", "Sub B", [], notes="")
    md = tm.to_markdown()
    assert "Task One → Sub A" in md
    assert "`a.cs`" in md
    assert "Task One → Sub B" in md


def test_to_markdown_empty_memory():
    tm = TaskMemory()
    assert tm.to_markdown() == "## Task Execution Summary"
