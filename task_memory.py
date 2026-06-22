class TaskMemory:
    def __init__(self):
        self.entries = []

    def add(self, task_title, subtask_title, changed_files, notes):
        self.entries.append({
            "task": task_title,
            "subtask": subtask_title,
            "changed_files": changed_files,
            "notes": notes,
        })

    def to_markdown(self):
        lines = ["## Task Execution Summary"]
        for e in self.entries:
            lines.append(f"- **{e['task']} → {e['subtask']}**")
            for f in e["changed_files"]:
                lines.append(f"  - `{f['path']}`")
        return "\n".join(lines)
