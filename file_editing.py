from pathlib import Path
from typing import List, Dict, Any

def apply_file_edits_for_task(repo_path: Path, file_edits: List[Dict[str, Any]]) -> None:
    """
    file_edits: [
      {"path": "src/Modules/...", "action": "modify", "content": "..."},
      {"path": "src/Modules/...", "action": "create", "content": "..."},
      {"path": "src/Modules/...", "action": "delete"},
    ]
    """
    for edit in file_edits:
        rel_path = Path(edit["path"])
        full_path = repo_path / rel_path

        action = edit.get("action", "modify")

        if action in ("create", "modify"):
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(edit["content"], encoding="utf-8")
        elif action == "delete":
            if full_path.exists():
                full_path.unlink()
