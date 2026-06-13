from pathlib import Path

def detect_repo_type(repo_path: Path) -> str:
    if (repo_path / "package.json").exists():
        return "frontend"
    if any(repo_path.glob("*.sln")):
        return "backend"
    return "unknown"
