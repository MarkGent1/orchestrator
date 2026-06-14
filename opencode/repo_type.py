from pathlib import Path

def detect_repo_type(repo_path: Path) -> str:
    """
    Detect whether the repository is a backend (.NET), frontend (Node/React),
    or a monorepo containing both.
    """

    has_sln = any(repo_path.glob("*.sln"))
    has_slnx = any(repo_path.glob("*.slnx"))
    has_csproj = any(repo_path.rglob("*.csproj"))

    has_package_json = (repo_path / "package.json").exists()
    has_frontend_folder = (repo_path / "frontend").exists()
    has_backend_folder = (repo_path / "backend").exists()

    # Detect .NET backend
    if has_sln or has_slnx or has_csproj or has_backend_folder:
        backend = True
    else:
        backend = False

    # Detect Node/React frontend
    if has_package_json or has_frontend_folder:
        frontend = True
    else:
        frontend = False

    # Monorepo
    if backend and frontend:
        return "fullstack"

    if backend:
        return "backend"

    if frontend:
        return "frontend"

    return "unknown"
