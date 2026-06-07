import subprocess
from pathlib import Path
from typing import Tuple

def run_backend_build(repo_path: Path) -> Tuple[bool, str]:
    proc = subprocess.Popen(
        ["dotnet", "build", "--no-restore"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = proc.communicate()[0]
    return proc.returncode == 0, output
