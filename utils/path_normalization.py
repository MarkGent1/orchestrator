import re
from pathlib import PurePosixPath, Path

def normalize_path_casing(rel_path: str, repo_type: str = None, workspace_root: Path = None) -> str:
    """
    Normalizes folder casing according to repo type, BUT preserves existing folder casing
    in the workspace. Only applies casing rules to NEW folders that do not already exist.

    - Backend (C#) → PascalCase for new folders
    - Frontend (JS/TS) → camelCase for new folders
    - Existing folders keep their real casing
    - Filenames keep their original casing
    """

    # Always use forward slashes
    rel_path = rel_path.replace("\\", "/")
    path = PurePosixPath(rel_path)
    parts = list(path.parts)

    normalized_parts = []
    current_path = workspace_root if workspace_root else None

    for part in parts:
        # Skip empty or root-like parts
        if part in ("", "."):
            normalized_parts.append(part)
            continue

        # Detect files by extension (not by dots in folder names)
        if "." in part and not part.endswith("/"):
            normalized_parts.append(part)
            continue

        # If we know the workspace root, check if this folder already exists.
        # current_path itself may not exist yet -- e.g. the model is
        # creating a brand new two-levels-deep folder such as
        # "NewSub/Deeper/File.cs" where "NewSub" doesn't exist on disk.
        # iterdir() on a non-existent path raises FileNotFoundError, so
        # guard with exists() and just fall through to the "new folder"
        # casing logic below in that case.
        if current_path and current_path.exists():
            # Look for a folder with ANY casing that matches this name
            existing = None
            for child in current_path.iterdir():
                if child.is_dir() and child.name.lower() == part.lower():
                    existing = child.name  # preserve real casing
                    break

            if existing:
                normalized_parts.append(existing)
                current_path = current_path / existing
                continue

        # NEW folder → apply repo-type casing rules
        name = part

        if repo_type == "backend":
            # PascalCase
            segments = re.split(r"[-_]", name)
            name = "".join(seg.capitalize() for seg in segments)

        elif repo_type == "frontend":
            # camelCase
            segments = re.split(r"[-_]", name)
            name = segments[0].lower() + "".join(seg.capitalize() for seg in segments[1:])

        normalized_parts.append(name)

        if current_path:
            current_path = current_path / name

    return "/".join(normalized_parts)
