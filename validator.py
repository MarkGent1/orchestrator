from typing import Tuple
from repo_type import detect_repo_type
from build_runner import BuildRunner
from test_runner import TestRunner
from fix_loop import FixLoop
from file_editing import apply_file_edits

class BuildTestValidator:
    """
    Runs build + tests, and if they fail, uses OpenCode to fix issues
    and retries up to max_attempts.
    """
    def __init__(self, repo_path: str, max_fix_attempts: int = 3):
        self.repo_path = repo_path
        self.repo_type = detect_repo_type(repo_path)

        self.build_runner = BuildRunner(repo_path, self.repo_type)
        self.test_runner = TestRunner(repo_path, self.repo_type)
        self.fix_loop = FixLoop(repo_path, max_attempts=max_fix_attempts)

    async def run_validation(self) -> Tuple[bool, str]:
        # 1. Build
        build_ok, build_output = self.build_runner.run()
        print("\n=== Build Output ===")
        print(build_output)
        print("====================\n")

        if not build_ok:
            ok, msg = await self._fix_and_retry(build_output, phase="build")
            return ok, msg

        # 2. Test
        test_ok, test_output = self.test_runner.run()
        print("\n=== Test Output ===")
        print(test_output)
        print("===================\n")

        if not test_ok:
            ok, msg = await self._fix_and_retry(test_output, phase="test")
            return ok, msg

        return True, "Build & tests passed"

    async def _fix_and_retry(self, error_output: str, phase: str) -> Tuple[bool, str]:
        """
        Try to fix errors using OpenCode, apply edits, and rerun build+tests.
        """
        for attempt in range(1, self.fix_loop.max_attempts + 1):
            print(f"\n=== Fix attempt {attempt} for {phase} errors ===")
            fixes = await self.fix_loop.attempt_fix(error_output)

            if not fixes:
                return False, f"No fix possible for {phase} errors"

            # Apply fixes
            apply_file_edits(self.repo_path, fixes)

            # Re-run build
            build_ok, build_output = self.build_runner.run()
            print("\n=== Build Output (after fix) ===")
            print(build_output)
            print("================================\n")

            if not build_ok:
                error_output = build_output
                continue

            # Re-run tests
            test_ok, test_output = self.test_runner.run()
            print("\n=== Test Output (after fix) ===")
            print(test_output)
            print("================================\n")

            if test_ok:
                return True, "Fixed and validated"

            error_output = test_output

        return False, f"Fix loop exhausted for {phase} errors"
