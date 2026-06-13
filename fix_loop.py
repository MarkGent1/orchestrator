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
        prompt = f"""
You are OpenCode Fixer.

The build or test run failed.

Here is the error output:

{error_output}

Return ONLY a JSON array of file edits that fix the issue.
If no fix is possible, return [].
Each edit must include: "file", "instructions", and "content".
"""
        return await call_opencode(prompt)
