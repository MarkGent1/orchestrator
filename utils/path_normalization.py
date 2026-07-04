import re
from pathlib import PurePosixPath, Path


def _smart_segment_case(segment: str, capitalize_first: bool) -> str:
    """
    Applies casing to a single already-split ('-'/'_' separated)
    path-segment token.

    If the segment is unambiguous (all-lowercase or ALL-UPPERCASE),
    there's no existing intentional casing to preserve, so the
    standard transform applies: force the first letter's case and
    lowercase the rest.

    If the segment already has mixed case (e.g. "RandomFolder",
    "myThing"), that mix is a strong signal the caller already
    intended a specific casing (PascalCase/camelCase) -- only the
    first letter is adjusted, and everything after it is left alone.

    This matters because str.capitalize() -- the previous
    implementation -- unconditionally lowercases every character
    after the first. Applied to an already-correct multi-word name
    with no separators (e.g. a model proposing a new "RandomFolder"
    or "NewWidgets" directory), that silently corrupted it to
    "Randomfolder" / "newwidgets", destroying the interior capital
    letters instead of leaving a already-well-formed name alone.
    """
    if not segment:
        return segment

    if segment.isupper() or segment.islower():
        transformed = segment[:1].upper() + segment[1:].lower()
    else:
        transformed = segment[:1].upper() + segment[1:]

    if not capitalize_first:
        transformed = transformed[:1].lower() + transformed[1:]

    return transformed


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
            # PascalCase: every segment's first letter is capitalized.
            segments = re.split(r"[-_]", name)
            name = "".join(
                _smart_segment_case(seg, capitalize_first=True) for seg in segments
            )

        elif repo_type == "frontend":
            # camelCase: only the very first segment stays lowercase-led.
            segments = re.split(r"[-_]", name)
            name = "".join(
                _smart_segment_case(seg, capitalize_first=(i > 0))
                for i, seg in enumerate(segments)
            )

        normalized_parts.append(name)

        if current_path:
            current_path = current_path / name

    return "/".join(normalized_parts)
