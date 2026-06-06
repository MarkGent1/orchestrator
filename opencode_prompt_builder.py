from pathlib import Path
from typing import Dict, Any, List

def detect_repo_type(repo_path: Path) -> str:
    if any(repo_path.glob("*.sln")):
        return "dotnet-backend"
    if (repo_path / "package.json").exists():
        return "frontend-js"
    return "unknown"

def build_repo_context(repo_path: Path) -> Dict[str, Any]:
    # minimal version: just list files under src/ and tests/
    src_root = repo_path / "src"
    tests_root = repo_path / "tests"

    def list_files(root: Path) -> List[str]:
        if not root.exists():
            return []
        return [
            str(p.relative_to(repo_path))
            for p in root.rglob("*")
            if p.is_file()
        ]

    return {
        "srcFiles": list_files(src_root),
        "testFiles": list_files(tests_root),
    }

async def build_opencode_prompt_for_task(
    repo_path: Path,
    work_item_id: int,
    work_item_title: str,
    task: Dict[str, Any],
) -> str:
    repo_type = detect_repo_type(repo_path)
    context = build_repo_context(repo_path)

    # You’ll tune this prompt over time; this is a solid starting point.
    prompt = f"""
You are an AI developer working on a {repo_type} repository that follows Clean Architecture.

Work Item:
- ID: {work_item_id}
- Title: {work_item_title}

Task:
- Title: {task['title']}
- Description: {task.get('description', '')}

Repository path: {repo_path}

Repository context:
- src files: {context['srcFiles']}
- test files: {context['testFiles']}

Requirements:
- Respect Clean Architecture boundaries (Core, Application, Infrastructure, API, Modules).
- For .NET backends, keep domain logic in Core/Application, infrastructure concerns in Infrastructure, and thin API surfaces.
- For frontend repos, keep components, hooks, and API routes idiomatic to React/Next.js.

Output format:
Return a JSON array of file edits. Each item must have:
- "path": relative path from repo root (e.g. "src/Modules/Cads.Cds.Api/Cads.Cds.Api.Application/Users/GetUserHandler.cs")
- "action": one of "create", "modify", "delete"
- "content": full file content for create/modify; omit for delete.

Do NOT include explanations, only the JSON array.
"""
    return prompt
