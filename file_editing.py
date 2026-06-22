import json
from pathlib import Path
from typing import List, Dict, Any
from utils.path_normalization import normalize_path_casing

def apply_file_edits_for_task(
    workspace_path: Path,
    file_edits: List[Dict[str, Any]],
    repo_type: str
) -> List[Dict[str, Any]]:
    """
    Applies OpenCode file edits into the TEMP workspace only.
    Returns a list of changed files for GitHub MCP commitFiles.
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

        rel_path = normalize_path_casing(path, repo_type)
        full_path = workspace_path / rel_path
        action = edit.get("instructions", "modify")

        if action in ("create", "modify"):
            full_path.parent.mkdir(parents=True, exist_ok=True)

            raw = edit["content"]
            content = json.loads(f'"{raw}"')

            full_path.write_text(content, encoding="utf-8")

            changed_files.append({
                "path": rel_path,
                "content": content,
            })

        elif action == "delete":
            # Delete from temp workspace only
            if full_path.exists():
                full_path.unlink()

            changed_files.append({
                "path": rel_path,
                "content": None,
            })

    return changed_files
