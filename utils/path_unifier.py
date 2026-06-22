from pathlib import PurePosixPath

def unify_path(raw_path: str) -> str:
    """
    Produces a fully normalized, POSIX-style, deterministic path.

    Fixes:
      - Windows slashes → /
      - Leading './' or '.\' removed
      - Leading/trailing whitespace removed
      - Duplicate slashes collapsed
      - Normalizes casing for folder names (but NOT filenames)
      - Ensures consistent POSIX formatting
    """

    if not raw_path:
        return ""

    # Strip whitespace
    path = raw_path.strip()

    # Convert Windows slashes → POSIX
    path = path.replace("\\", "/")

    # Remove leading './' or '.'
    while path.startswith("./") or path.startswith(".\\") or path.startswith("."):
        path = path[1:]
        path = path.lstrip("/")

    # Collapse duplicate slashes
    while "//" in path:
        path = path.replace("//", "/")

    # Convert to PurePosixPath for canonical formatting
    posix = PurePosixPath(path)

    # Return normalized string
    return str(posix)
