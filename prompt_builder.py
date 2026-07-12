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

# Used only for the repo TREE shown to the model (paths only, no file
# content) -- unlike EXCLUDED_DIRS above, this does NOT exclude
# "tests". Excluding tests/ from collect_relevant_files() keeps full
# file content out of the prompt (existing test suites can be large),
# but excluding it from the tree too made every existing test project
# under tests/ invisible to the model. When asked to "add a unit
# test", the model had no way to see that e.g.
# tests/Mav.UserMgmt.Api.Unit.Tests/ already exists and would invent a
# brand new test project under src/ instead -- which Clean
# Architecture enforcement then correctly rejects as an illegal new
# module, crashing the run. Showing the tree (without the content)
# is enough for the model to place new test files alongside the
# existing ones.
TREE_EXCLUDED_DIRS = {
    "bin",
    "obj",
    ".github",
    ".git",
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
                # Force forward slashes regardless of host OS -- str()
                # on a WindowsPath renders "\\"-separated, which would
                # be inconsistent with every other path shown to the
                # model in this prompt (JSON edit paths, test
                # placement rules, the repo tree below all use "/").
                "path": str(full_path.relative_to(repo_path)).replace("\\", "/"),
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
        dirs[:] = [d for d in dirs if d not in TREE_EXCLUDED_DIRS]
        for name in dirs + files:
            # Force forward slashes regardless of host OS -- on
            # Windows, str(WindowsPath(...)) renders "\\"-separated,
            # which would make the tree the model sees inconsistent
            # with every other forward-slash path in this same prompt
            # (JSON edit paths, test placement rules, etc.).
            rel = str((Path(root) / name).relative_to(repo_path)).replace("\\", "/")
            tree_entries.append(rel)
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
    # Test placement rules
    #
    # tests/ is exempt from Clean Architecture's module-boundary check
    # (CleanArchitectureEnforcer allows anything under tests/), so
    # without explicit guidance the model has no signal for WHERE
    # inside tests/ new test files belong, or that it must reuse an
    # existing test project rather than inventing one. The repo tree
    # above now includes the tests/ folder specifically so the model
    # can see existing test project names/paths to match.
    # ---------------------------------------------------------
    test_placement_rules = """
### Test Placement Rules (MANDATORY)
- Test files belong under an EXISTING test project inside tests/ (see
  the Repository Tree above for the exact existing project names,
  e.g. tests/<Module>.Unit.Tests/, tests/<Module>.Integration.Tests/).
- Match the existing project's folder structure and namespace
  convention for the file you are adding (e.g. a test for
  Controllers/FooController.cs typically belongs under that project's
  Controllers/ subfolder).
- You MUST NOT create a new test project, a new .csproj/package.json,
  or any new top-level folder for tests. If no existing test project
  looks like a fit, add the file to the closest existing one instead.
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

{test_placement_rules}
"""

    # ---------------------------------------------------------
    # Frontend rules
    # ---------------------------------------------------------
    frontend_rules = f"""
### Frontend (React / Next.js / TypeScript) Rules
- Use functional components.
- Use TypeScript strict mode.
- Use interfaces/types for props.
- Use app router conventions.
- Generate ONLY .ts/.tsx files.
- NEVER generate C# code.

{test_placement_rules}
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
