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

Repository root:
{self.repo_path}

Here is the error output:

{error_output}

Return ONLY a JSON array of file edits that fix the issue.
If no fix is possible, return [].

Each edit MUST have:
- "file": relative path from the repository root
- "instructions": one of "create", "modify", "delete"
- "content": full file content for create/modify; any value for delete

Your output must ALWAYS be valid JSON.
"""

        edits = await call_opencode(prompt)

        if not isinstance(edits, list):
            raise TypeError(f"Expected a JSON array of edits, got: {type(edits)}")

        for e in edits:
            if "instructions" not in e:
                raise ValueError("FixLoop: missing 'instructions' field in edit")

        return edits
