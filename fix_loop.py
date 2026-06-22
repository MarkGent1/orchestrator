from typing import List, Dict, Any
from pathlib import Path

from opencode.client import call_opencode
from architecture.enforcement import CleanArchitectureEnforcer


class FixLoop:
    """
    Given build/test errors, asks OpenCode to generate file edits that fix them.
    """

    def __init__(
        self,
        repo_path: str,
        max_attempts: int = 3,
        repo_type: str = None,
        enforcer: CleanArchitectureEnforcer = None,
    ):
        self.repo_path = Path(repo_path)      # temp workspace
        self.max_attempts = max_attempts
        self.repo_type = repo_type            # backend or frontend
        self.enforcer = enforcer              # Clean Architecture enforcement layer

    async def attempt_fix(self, error_output: str) -> List[Dict[str, Any]]:
        if self.repo_type == "backend":
            language_rules = f"""
### CRITICAL LANGUAGE RULES
This is a BACKEND C#/.NET repository.
You MUST generate ONLY C# code.
You MUST generate ONLY .cs files.
You MUST NOT generate TypeScript, JavaScript, NestJS, Node.js, Python, or any non-C# code.

### CLEAN ARCHITECTURE RULES (MANDATORY)
This repository follows a modular Clean Architecture structure.

You MUST obey these rules:

1. All backend code MUST live inside an existing module folder under:
   src/<ModuleName>/

   A module is defined as any folder directly under src/ that contains a .csproj file.

2. You MUST NOT create new top-level folders under src/.
3. You MUST place new files ONLY inside an existing module.
4. Inside a module, you MAY create ONLY these folders:
   - Controllers
   - Models
   - DTOs
   - Services
   - Interfaces
   - Setup
   - Extensions

5. You MUST NOT create new modules.
6. You MUST NOT move files outside their module.
7. All file paths MUST be relative to the repository root and MUST match the existing folder structure.
8. All folder names MUST follow backend naming conventions:
   - PascalCase for folders
   - PascalCase for C# files
   - Interfaces MUST start with "I"
   - DTOs MUST end with "Dto"
   - Controllers MUST end with "Controller"
   - Services MUST end with "Service"

### MODULE STRUCTURE (DETECTED)
{self.enforcer.describe_modules() if self.enforcer else "(No module info available)"}

### SAFETY RULES
- Prefer minimal, targeted changes over large rewrites.
- DO NOT modify .csproj files unless the error message explicitly mentions missing packages or project references.
- DO NOT remove existing services, controllers, or models unless the error message clearly indicates they are invalid.
"""
        elif self.repo_type == "frontend":
            language_rules = """
### CRITICAL LANGUAGE RULES
This is a FRONTEND TypeScript/React repository.
You MUST generate ONLY .ts/.tsx files.
You MUST NOT generate C# code.

### SAFETY RULES
- Prefer minimal, targeted changes over large rewrites.
"""
        else:
            language_rules = "### Unknown repo type — generate minimal safe fixes only."

        prompt = f"""
You are OpenCode Fixer.

The build or test run failed.

Repository root:
{self.repo_path}

Here is the error output:

{error_output}

{language_rules}

### Output Format (MANDATORY)
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

        safe_edits: List[Dict[str, Any]] = []

        for e in edits:
            if "instructions" not in e:
                raise ValueError("FixLoop: missing 'instructions' field in edit")

            file_path = (
                e.get("file")
                or e.get("path")
                or e.get("file_path")
                or e.get("new_file")
                or e.get("filename")
            )

            if not file_path:
                raise ValueError(f"FixLoop: edit missing file path: {e}")

            # Clean Architecture enforcement
            if self.enforcer and not self.enforcer.validate_path(file_path):
                raise ValueError(
                    f"FixLoop generated illegal backend path under Clean Architecture rules: {file_path}"
                )

            safe_edits.append(e)

        return safe_edits
