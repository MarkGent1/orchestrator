import subprocess
from pathlib import Path
from typing import Tuple

def run_frontend_build(repo_path: Path) -> Tuple[bool, str]:
    # Try to install dependencies, but do NOT crash the orchestrator
    install_proc = subprocess.Popen(
        ["npm", "install"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    install_output = install_proc.communicate()[0]

    # Always attempt the build, even if install failed
    proc = subprocess.Popen(
        ["npm", "run", "build"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = install_output + "\n\n" + proc.communicate()[0]

    return proc.returncode == 0, output
