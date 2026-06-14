import subprocess
from pathlib import Path
from typing import Tuple

def run_backend_build(repo_path: Path) -> Tuple[bool, str]:
    # Find .sln or .slnx
    sln_files = list(repo_path.glob("*.sln")) + list(repo_path.glob("*.slnx"))
    if not sln_files:
        return False, "No solution file (.sln or .slnx) found"

    sln = sln_files[0]

    proc = subprocess.Popen(
        ["dotnet", "build", str(sln), "--no-restore"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = proc.communicate()[0]
    return proc.returncode == 0, output
