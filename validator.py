from pathlib import Path

from backend_build import run_backend_build
from backend_test import run_backend_tests

from frontend_build import run_frontend_build
from frontend_test import run_frontend_tests
from frontend_lint import run_frontend_lint
from frontend_format import run_frontend_format

from fix_loop import FixLoop
from file_editing import apply_file_edits_for_task
from architecture.enforcement import CleanArchitectureEnforcer

class BuildTestValidator:
    def __init__(
        self,
        repo_path: Path,
        temp_workspace: Path,
        max_fix_attempts: int = 3,
        repo_type: str = None,
        enforcer: CleanArchitectureEnforcer = None,
        model_config: object = None
    ):
        self.repo_path = repo_path
        self.temp_workspace = temp_workspace
        self.repo_type = repo_type
        self.max_fix_attempts = max_fix_attempts
        self.model_config = model_config
        self.enforcer = enforcer

        # Pass model_config into FixLoop
        self.fix_loop = FixLoop(
            self.temp_workspace,
            max_fix_attempts,
            self.repo_type,
            enforcer,
            model_config=self.model_config
        )

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
        elif self.repo_type == "fullstack":
            # Run both sets of phases. repo_type.py can detect a
            # monorepo containing both a .NET backend and a Node
            # frontend, but this branch didn't exist before -- any
            # fullstack repo would always hit the "Unknown repo type"
            # case below and fail validation outright, no matter how
            # clean the actual build was.
            phases = [
                ("backend build", run_backend_build),
                ("backend test", run_backend_tests),
                ("frontend build", run_frontend_build),
                ("frontend test", run_frontend_tests),
                ("frontend lint", run_frontend_lint),
                ("frontend format", run_frontend_format),
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

            # FixLoop now uses dynamic model selection. attempt_fix()
            # itself validates each proposed edit's path against Clean
            # Architecture rules and raises ValueError on an illegal
            # one -- this used to propagate all the way out of
            # run_validation() and crash the whole orchestrator run,
            # the same "Illegal raw path from model" failure mode that
            # task_executor.py was fixed for. Contain it here instead:
            # treat an illegal proposal as a failed attempt and let the
            # loop retry, rather than losing all validation progress.
            try:
                fixes = await self.fix_loop.attempt_fix(error_output)
            except ValueError as ex:
                print(
                    f"--- Fix attempt {attempt} for {phase_name} proposed an invalid "
                    f"edit and was skipped: {ex} ---"
                )
                continue

            if not fixes:
                return False, f"No fix possible for {phase_name} errors"

            # apply_file_edits_for_task() already resolves the path
            # field (file/path/file_path/new_file/filename), unifies
            # it, and applies casing normalization -- doing that again
            # here first and handing it an already-normalized "path"
            # would run normalize_path_casing() twice on the same
            # value. For brand-new multi-segment folder names that is
            # not a no-op (str.capitalize() lowercases the rest of an
            # already-PascalCased name on the second pass), so this
            # previously risked mangling freshly-created folder names
            # in the fix-loop path specifically.
            #
            # This can also raise ValueError (a path that only becomes
            # illegal after casing normalization, bad content type, an
            # unknown instruction, etc.) -- contained the same way as
            # the attempt_fix() call above.
            try:
                apply_file_edits_for_task(
                    self.temp_workspace,
                    fixes,
                    self.repo_type,
                    enforcer=self.enforcer,
                )
            except ValueError as ex:
                print(
                    f"--- Fix attempt {attempt} for {phase_name} produced an invalid "
                    f"edit and was skipped: {ex} ---"
                )
                continue

            ok, output = runner(self.temp_workspace)
            print(f"\n=== {phase_name.upper()} OUTPUT (after fix) ===\n{output}\n")

            if ok:
                return True, f"{phase_name} fixed"

            error_output = output

        return False, f"Fix loop exhausted for {phase_name}"
