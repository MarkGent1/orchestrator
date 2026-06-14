from pathlib import Path
import json
from .repo_type import detect_repo_type

# Utility: collect relevant files for context
def collect_relevant_files(repo_path: Path, max_files: int = 40):
    exts = [".cs", ".csproj", ".sln", ".ts", ".tsx", ".js", ".jsx", ".json", ".yml", ".yaml", ".md"]
    files = []

    for ext in exts:
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
):
    repo_type = detect_repo_type(repo_path)
    repo_tree = "\n".join([str(p.relative_to(repo_path)) for p in repo_path.rglob("*")][:200])
    relevant_files = collect_relevant_files(repo_path)

    # ---------------------------------------------------------
    # Backend conventions (Clean Architecture)
    # ---------------------------------------------------------
    backend_rules = """
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
