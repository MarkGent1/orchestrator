from pathlib import Path
import json

from architecture.enforcement import CleanArchitectureEnforcer


# ============================================================
# File Collection (Backend + Frontend)
# ============================================================

BACKEND_ALLOWED_DIRS = {
    "Controllers",
    "Interfaces",
    "Services",
    "Models",
    "DTOs",
    "Setup",
    "Extensions",
}

FRONTEND_ALLOWED_DIRS = {
    "src",
    "app",
    "components",
    "hooks",
    "lib",
    "utils",
}

BACKEND_EXTS = {".cs"}
FRONTEND_EXTS = {".ts", ".tsx"}

EXCLUDED_DIRS = {
    "bin",
    "obj",
    ".github",
    ".git",
    "tests",
    "node_modules",
    "dist",
    "build",
}

EXCLUDED_EXTS = {
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".sln",
    ".csproj",
    ".lock",
    ".config",
    ".dockerignore",
    ".gitignore",
}


def collect_relevant_files(repo_path: Path, repo_type: str, max_files: int = 200):
    relevant = []

    for root, dirs, files in repo_path.walk():
        # Remove excluded dirs
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        # Backend filtering
        if repo_type == "backend":
            if not any(part in BACKEND_ALLOWED_DIRS for part in Path(root).parts):
                continue
            allowed_exts = BACKEND_EXTS

        # Frontend filtering
        elif repo_type == "frontend":
            if not any(part in FRONTEND_ALLOWED_DIRS for part in Path(root).parts):
                continue
            allowed_exts = FRONTEND_EXTS

        else:
            allowed_exts = BACKEND_EXTS | FRONTEND_EXTS

        for file in files:
            ext = Path(file).suffix

            if ext in EXCLUDED_EXTS:
                continue

            if ext not in allowed_exts:
                continue

            full_path = Path(root) / file
            try:
                content = full_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""

            relevant.append({
                "path": str(full_path.relative_to(repo_path)),
                "content": content
            })

            if len(relevant) >= max_files:
                return relevant

    return relevant


# ============================================================
# Prompt Builder
# ============================================================

async def build_opencode_prompt_for_task(
    repo_path: Path,
    work_item_id: int,
    work_item_title: str,
    task: dict,
    repo_type: str,
    enforcer: CleanArchitectureEnforcer,
):
    if repo_type == "backend" and enforcer is None:
        raise ValueError("PromptBuilder requires CleanArchitectureEnforcer for backend repos.")

    # ---------------------------------------------------------
    # Repo tree (trimmed)
    #
    # Walk with the same EXCLUDED_DIRS pruning used by
    # collect_relevant_files(). A plain rglob("*") would include
    # bin/obj/node_modules/.git, which for a freshly-restored .NET
    # project can easily contain thousands of entries -- so the first
    # 150 lines of "tree" the model sees would be build output noise
    # instead of actual source layout.
    # ---------------------------------------------------------
    tree_entries = []
    for root, dirs, files in repo_path.walk():
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for name in dirs + files:
            tree_entries.append(str((Path(root) / name).relative_to(repo_path)))
            if len(tree_entries) >= 150:
                break
        if len(tree_entries) >= 150:
            break

    repo_tree = "\n".join(tree_entries)

    # ---------------------------------------------------------
    # Relevant files (filtered)
    # ---------------------------------------------------------
    relevant_files = collect_relevant_files(repo_path, repo_type)

    # ---------------------------------------------------------
    # Module structure (backend only)
    # ---------------------------------------------------------
    module_rules = ""
    if repo_type == "backend":
        module_rules = f"""
### MODULE STRUCTURE (DETECTED)
{enforcer.describe_modules()}

You MUST place all backend code inside an existing module under src/<ModuleName>/.
You MUST NOT create new modules.
You MUST NOT place backend code outside its module.
"""

    # ---------------------------------------------------------
    # Backend rules
    # ---------------------------------------------------------
    backend_rules = f"""
### Backend (.NET) Architecture Rules
- Follow Clean Architecture.
- Controllers are thin.
- Services contain logic.
- Interfaces define contracts.
- Use dependency injection.
- Generate ONLY C# (.cs) files.
- NEVER generate JS/TS/Python.

{module_rules}
"""

    # ---------------------------------------------------------
    # Frontend rules
    # ---------------------------------------------------------
    frontend_rules = """
### Frontend (React / Next.js / TypeScript) Rules
- Use functional components.
- Use TypeScript strict mode.
- Use interfaces/types for props.
- Use app router conventions.
- Generate ONLY .ts/.tsx files.
- NEVER generate C# code.
"""

    # ---------------------------------------------------------
    # Repo-type specific rules
    # ---------------------------------------------------------
    if repo_type == "backend":
        repo_specific = backend_rules
    elif repo_type == "frontend":
        repo_specific = frontend_rules
    else:
        repo_specific = "### Unknown repo type — generate minimal safe edits only."

    # ---------------------------------------------------------
    # JSON-only contract
    # ---------------------------------------------------------
    json_contract = """
### Output Format (MANDATORY)
Return ONLY a JSON array of file edits:

[
  {
    "file": "relative/path/to/file",
    "instructions": "create|modify|delete",
    "content": "full file content after edit (ignored for delete)"
  }
]

If no edits are needed, return [].
"""

    # ---------------------------------------------------------
    # Final prompt
    # ---------------------------------------------------------
    prompt = f"""
You are OpenCode — an AI software engineer.

### Work Item {work_item_id}
{work_item_title}

### Task
{task['title']}
{task.get('description', '')}

### Repository Type
{repo_type}

### Repository Tree (partial)
{repo_tree}

### Relevant Files (filtered)
{json.dumps(relevant_files, indent=2)}

{repo_specific}

{json_contract}

### Your Goal
Generate the minimal set of file edits required to implement the task.
Follow all conventions.
Always return valid JSON.
"""

    return prompt
