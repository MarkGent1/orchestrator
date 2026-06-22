import subprocess
from pathlib import Path
from typing import Tuple

def run_backend_tests(repo_path: Path) -> Tuple[bool, str]:
    # Find .sln or .slnx anywhere in the workspace
    sln_files = list(repo_path.rglob("*.sln")) + list(repo_path.rglob("*.slnx"))
    if not sln_files:
        return False, "No solution file (.sln or .slnx) found"

    sln = sln_files[0]

    proc = subprocess.Popen(
        ["dotnet", "test", str(sln), "--no-build"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = proc.communicate()[0]
    return proc.returncode == 0, output
