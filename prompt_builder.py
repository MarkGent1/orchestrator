from pathlib import Path
import json

from architecture.enforcement import CleanArchitectureEnforcer

# Utility: collect relevant files for context
def collect_relevant_files(repo_path: Path, max_files: int = 300):
    # PRIORITY ORDER: C# project files first
    priority_exts = [".csproj", ".sln", ".cs"]
    secondary_exts = [".json", ".yml", ".yaml", ".md", ".ts", ".tsx", ".js", ".jsx"]

    files = []

    # First pass: C# project files and code
    for ext in priority_exts:
        for f in repo_path.rglob(f"*{ext}"):
            if len(files) >= max_files:
                return files
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except:
                content = ""
            files.append({"path": str(f.relative_to(repo_path)), "content": content})

    # Second pass: supporting files
    for ext in secondary_exts:
        for f in repo_path.rglob(f"*{ext}"):
            if len(files) >= max_files:
                return files
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except:
                content = ""
            files.append({"path": str(f.relative_to(repo_path)), "content": content})

    return files


async def build_opencode_prompt_for_task(
    repo_path: Path,
    work_item_id: int,
    work_item_title: str,
    task: dict,
    repo_type: str,
    enforcer: CleanArchitectureEnforcer,
):
    if repo_type == "backend" and enforcer is None:
        raise ValueError("PromptBuilder requires a CleanArchitectureEnforcer for backend repos.")

    # ---------------------------------------------------------
    # Repo tree + relevant files
    # ---------------------------------------------------------
    repo_tree = "\n".join(
        [str(p.relative_to(repo_path)) for p in repo_path.rglob("*")][:200]
    )
    relevant_files = collect_relevant_files(repo_path)

    # ---------------------------------------------------------
    # MODULE STRUCTURE (from enforcer)
    # ---------------------------------------------------------
    module_list = enforcer.describe_modules()

    module_rules = f"""
### MODULE STRUCTURE (DETECTED)
The repository contains the following backend modules:

{module_list}

A module is defined as any folder directly under src/ that contains a .csproj file.

You MUST place all backend code inside one of these modules.
You MUST NOT create new modules.
You MUST NOT place backend code outside src/<ModuleName>/.
"""

    # ---------------------------------------------------------
    # Backend conventions (Clean Architecture)
    # ---------------------------------------------------------
    backend_rules = f"""
### Backend (.NET) Architecture Rules
- Follow Clean Architecture.
- Domain layer is pure (no external dependencies).
- Application layer contains use cases, DTOs, interfaces.
- Infrastructure implements interfaces (repositories, clients).
- API layer is thin (controllers, minimal API).
- Modules follow vertical slice structure.
- No business logic in controllers.
- No direct EF Core usage in Application layer.
- Use dependency injection for all services.
- The DTO folder MUST be named exactly `DTOs` (uppercase).

### CRITICAL LANGUAGE RULES
This repository is a BACKEND C#/.NET project.
You MUST generate ONLY C# code.
You MUST generate ONLY .cs files.
You MUST NOT generate JavaScript, TypeScript, NestJS, Node.js, Python, or any non-C# code.

### CLEAN ARCHITECTURE RULES (MANDATORY)
This repository follows a modular Clean Architecture structure.

You MUST obey these rules:

1. All backend code MUST live inside an existing module folder under:
   src/<ModuleName>/

2. You MUST NOT create new top-level folders under src/.
   Forbidden examples:
   - src/Controllers
   - src/Models
   - src/DTOs
   - src/Services
   - src/<anything-else>

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

{module_rules}
"""

    # ---------------------------------------------------------
    # Frontend conventions (React / Next.js / TypeScript)
    # ---------------------------------------------------------
    frontend_rules = """
### Frontend (React / Next.js / TypeScript) Rules
- Use functional components only.
- Prefer hooks over classes.
- Use TypeScript strict mode.
- Use interfaces/types for props.
- Use React Server Components by default in Next.js (app router).
- Use "use client" only when needed.
- Place UI components in /components.
- Place hooks in /hooks.
- Place server actions in /app/<route>/actions.ts.
- Place API routes in /app/api/<route>/route.ts.
- Follow ESLint rules:
  - no-unused-vars
  - no-implicit-any
  - react/jsx-key
  - react-hooks/exhaustive-deps
- Follow Prettier formatting:
  - 2 spaces
  - trailing commas
  - semicolons
  - sorted imports

### CRITICAL LANGUAGE RULES
This repository is a FRONTEND TypeScript/React project.
You MUST generate ONLY .ts/.tsx files.
You MUST NOT generate C# code.
"""

    # ---------------------------------------------------------
    # Repo-type specific instructions
    # ---------------------------------------------------------
    if repo_type == "backend":
        repo_specific = backend_rules
    elif repo_type == "frontend":
        repo_specific = frontend_rules
    else:
        repo_specific = "### Unknown repo type — generate safe, minimal edits only."

    # ---------------------------------------------------------
    # JSON-only contract (critical)
    # ---------------------------------------------------------
    json_contract = """
### Output Format (MANDATORY)
Return ONLY a JSON array of file edits.

Each edit must be:
{
  "file": "relative/path/to/file",
  "instructions": "create|modify|delete|append",
  "content": "full file content after edit"
}

If no edits are needed, return [].
Never return explanations, markdown, or text outside the JSON array.
"""

    # ---------------------------------------------------------
    # Build final prompt
    # ---------------------------------------------------------
    prompt = f"""
You are OpenCode — an AI software engineer.

Your job is to implement the following task for Work Item {work_item_id}:

### Work Item
{work_item_title}

### Task
{task['title']}
{task.get('description', '')}

### Repository Type
{repo_type}

### Repository Tree (partial)
{repo_tree}

### Relevant Files (partial)
{json.dumps(relevant_files, indent=2)}

{repo_specific}

{json_contract}

### Your Goal
Implement the task by generating the minimal set of file edits required.
Follow all conventions for the detected repo type.
Ensure the output is ALWAYS valid JSON.
"""

    return prompt
