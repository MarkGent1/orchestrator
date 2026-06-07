import subprocess
from pathlib import Path

class TestRunner:
    def __init__(self, repo_path: Path, repo_type: str):
        self.repo_path = repo_path
        self.repo_type = repo_type

    def run(self):
        if self.repo_type == "backend":
            return self._run_dotnet_tests()
        if self.repo_type == "frontend":
            return self._run_frontend_tests()
        return False, "Unknown repo type"

    def _run_dotnet_tests(self):
        proc = subprocess.Popen(
            ["dotnet", "test", "--no-build"],
            cwd=self.repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output = proc.communicate()[0]
        return proc.returncode == 0, output

    def _run_frontend_tests(self):
        proc = subprocess.Popen(
            ["npm", "test", "--", "--watch=false"],
            cwd=self.repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        output = proc.communicate()[0]
        return proc.returncode == 0, output
