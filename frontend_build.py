import subprocess
from pathlib import Path
from typing import Tuple

def run_frontend_build(repo_path: Path) -> Tuple[bool, str]:
    # Ensure dependencies installed
    subprocess.run(["npm", "install"], cwd=repo_path)

    proc = subprocess.Popen(
        ["npm", "run", "build"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = proc.communicate()[0]
    return proc.returncode == 0, output
