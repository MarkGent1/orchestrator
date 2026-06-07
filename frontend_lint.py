import subprocess
from pathlib import Path
from typing import Tuple

def run_frontend_lint(repo_path: Path) -> Tuple[bool, str]:
    proc = subprocess.Popen(
        ["npm", "run", "lint"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = proc.communicate()[0]
    return proc.returncode == 0, output
