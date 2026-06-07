from pathlib import Path
from repo_type import detect_repo_type

from backend_build import run_backend_build
from backend_test import run_backend_tests

from frontend_build import run_frontend_build
from frontend_test import run_frontend_tests
from frontend_lint import run_frontend_lint
from frontend_format import run_frontend_format

from fix_loop import FixLoop
from file_editing import apply_file_edits_for_task


class BuildTestValidator:
    def __init__(self, repo_path: Path, max_fix_attempts: int = 3):
        self.repo_path = repo_path
        self.repo_type = detect_repo_type(repo_path)
        self.max_fix_attempts = max_fix_attempts
        self.fix_loop = FixLoop(repo_path, max_fix_attempts)

    async def run_validation(self):
        if self.repo_type == "backend":
            phases = [
                ("build", run_backend_build),
                ("test", run_backend_tests),
            ]

        elif self.repo_type == "frontend":
            phases = [
                ("build", run_frontend_build),
                ("test", run_frontend_tests),
                ("lint", run_frontend_lint),
                ("format", run_frontend_format),
            ]

        else:
            return False, f"Unknown repo type: {self.repo_type}"

        for phase_name, runner in phases:
            ok, output = runner(self.repo_path)
            print(f"\n=== {phase_name.upper()} OUTPUT ===\n{output}\n")

            if not ok:
                ok, msg = await self._fix_and_retry(phase_name, output, runner)
                if not ok:
                    return False, msg

        return True, "All validation steps passed"

    async def _fix_and_retry(self, phase_name, error_output, runner):
        for attempt in range(1, self.max_fix_attempts + 1):
            print(f"\n=== Fix attempt {attempt} for {phase_name} errors ===")

            fixes = await self.fix_loop.attempt_fix(error_output)
            if not fixes:
                return False, f"No fix possible for {phase_name} errors"

            apply_file_edits_for_task(self.repo_path, fixes)

            ok, output = runner(self.repo_path)
            print(f"\n=== {phase_name.upper()} OUTPUT (after fix) ===\n{output}\n")

            if ok:
                return True, f"{phase_name} fixed"

            error_output = output

        return False, f"Fix loop exhausted for {phase_name}"
