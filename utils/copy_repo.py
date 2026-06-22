import os
import shutil
from pathlib import Path

IGNORE_DIRS = {
    ".git",
    ".orchestrator-tmp",
    "bin",
    "obj",
    ".vs",
    ".idea",
    "node_modules",
    "TestResults",
}

def copy_repo_to_workspace(src: Path, dst: Path):
    for root, dirs, files in os.walk(src):

        # Remove ignored dirs from traversal
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        rel = Path(root).relative_to(src)
        target_dir = dst / rel
        target_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            shutil.copy2(Path(root) / f, target_dir / f)
