from pathlib import Path

def detect_repo_type(repo_path: Path) -> str:
    """
    Detect whether the repository is a backend (.NET) or frontend
    (Node/React) repo.

    Repos are always a single type with src/ and tests/ directly at
    the repository root -- there is no "frontend/" or "backend/"
    subfolder convention and no monorepo case to support. Detection
    used to also check for literal "frontend"/"backend" subfolders,
    which was both dead weight (those folders never exist in this
    convention) and a real misdetection risk: any unrelated folder
    that happened to be named "frontend" or "backend" (e.g. docs,
    fixtures) would have caused a plain single-type repo to be
    misclassified as "fullstack" and run the wrong validation phases.
    """

    has_sln = any(repo_path.glob("*.sln"))
    has_slnx = any(repo_path.glob("*.slnx"))
    has_csproj = any(repo_path.rglob("*.csproj"))
    backend = has_sln or has_slnx or has_csproj

    has_package_json = (repo_path / "package.json").exists()
    frontend = has_package_json

    # Both signals present at once shouldn't normally happen given the
    # single-type repo convention, but if it ever does (e.g. a .NET
    # repo with a root package.json used purely for tooling), don't
    # silently misclassify -- surface it as "fullstack" so validation
    # explicitly runs both sets of checks rather than guessing.
    if backend and frontend:
        return "fullstack"

    if backend:
        return "backend"

    if frontend:
        return "frontend"

    return "unknown"
