from pathlib import Path
from typing import List, Dict, Any

def apply_file_edits_for_task(
    repo_path: Path,
    file_edits: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Applies OpenCode file edits and returns a list of changed files
    in the format required by commitFiles:
    
    [
      {
        "path": "src/Modules/.../File.cs",
        "content": "<full file content>"
      }
    ]
    """

    changed_files = []

    for edit in file_edits:
        path = (
            edit.get("path")
            or edit.get("file")
            or edit.get("file_path")
            or edit.get("new_file")
            or edit.get("filename")
        )

        if not path:
            raise ValueError(f"Edit has no path-like field: {edit}")

        rel_path = Path(path)

        full_path = repo_path / rel_path
        action = edit.get("action", "modify")

        if action in ("create", "modify"):
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(edit["content"], encoding="utf-8")

            changed_files.append({
                "path": str(rel_path),
                "content": edit["content"],
            })

        elif action == "delete":
            if full_path.exists():
                full_path.unlink()

            changed_files.append({
                "path": str(rel_path),
                "content": None,  # GitHub MCP interprets None as delete
            })

    return changed_files
