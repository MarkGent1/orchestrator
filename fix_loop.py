from typing import List, Dict, Any

from opencode.client import call_opencode


class FixLoop:
    """
    Given build/test errors, asks OpenCode to generate file edits that fix them.
    """

    def __init__(self, repo_path: str, max_attempts: int = 3):
        self.repo_path = repo_path
        self.max_attempts = max_attempts

    async def attempt_fix(self, error_output: str) -> List[Dict[str, Any]]:
        """
        Returns a JSON array of file edits (or [] if no fix is possible).
        """
        base_prompt = f"""
You are OpenCode Fixer.

The build or test run failed.

Here is the error output:

{error_output}

Return ONLY a JSON array of file edits that fix the issue.
If no fix is possible, return [].
Each edit must include: "file", "instructions", and "content".
"""

        last_error: Exception | None = None

        for _ in range(self.max_attempts):
            try:
                edits = await call_opencode(base_prompt)
                # Defensive: ensure we always return a list
                if not isinstance(edits, list):
                    raise TypeError(f"Expected list of edits, got {type(edits)}")
                return edits
            except Exception as ex:
                last_error = ex
                continue

        # If we truly can't parse anything useful, surface the last error
        if last_error:
            raise last_error
        return []
