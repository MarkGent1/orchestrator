from pathlib import Path

from backend_build import run_backend_build
from backend_test import run_backend_tests

from frontend_build import run_frontend_build
from frontend_test import run_frontend_tests
from frontend_lint import run_frontend_lint
from frontend_format import run_frontend_format

from fix_loop import FixLoop
from file_editing import apply_file_edits_for_task
from utils.path_normalization import normalize_path_casing
from architecture.enforcement import CleanArchitectureEnforcer

class BuildTestValidator:
    def __init__(
        self,
        repo_path: Path,
        temp_workspace: Path,
        max_fix_attempts: int = 3,
        repo_type: str = None,
        enforcer: CleanArchitectureEnforcer = None,
    ):
        self.repo_path = repo_path
        self.temp_workspace = temp_workspace
        self.repo_type = repo_type
        self.max_fix_attempts = max_fix_attempts
        self.fix_loop = FixLoop(self.temp_workspace, max_fix_attempts, self.repo_type, enforcer)

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
            ok, output = runner(self.temp_workspace)
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

            for fix in fixes:
                file_path = (
                    fix.get("file")
                    or fix.get("path")
                    or fix.get("file_path")
                    or fix.get("new_file")
                    or fix.get("filename")
                )

                if not file_path:
                    raise ValueError(f"FixLoop returned an edit without a file path: {fix}")

                normalized = normalize_path_casing(
                    file_path,
                    self.repo_type,
                    workspace_root=self.temp_workspace,
                )

                fix["path"] = normalized

            apply_file_edits_for_task(self.temp_workspace, fixes, self.repo_type)

            ok, output = runner(self.temp_workspace)
            print(f"\n=== {phase_name.upper()} OUTPUT (after fix) ===\n{output}\n")

            if ok:
                return True, f"{phase_name} fixed"

            error_output = output

        return False, f"Fix loop exhausted for {phase_name}"
