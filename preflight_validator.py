from pathlib import Path
import subprocess
from typing import Tuple


def fail(message: str) -> Tuple[bool, str]:
    return False, f"Pre-flight failed: {message}"


def run(cmd: list[str], cwd: Path) -> Tuple[bool, str]:
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output = proc.communicate()[0]
    return proc.returncode == 0, output


# ---------------------------------------------------------
# Backend detection
# ---------------------------------------------------------
def detect_backend(repo_path: Path) -> Path | None:
    sln_files = list(repo_path.glob("*.sln")) + list(repo_path.glob("*.slnx"))
    if sln_files:
        return sln_files[0]
    return None


# ---------------------------------------------------------
# Frontend detection
# ---------------------------------------------------------
def detect_frontend(repo_path: Path) -> Path | None:
    # Root-level package.json
    if (repo_path / "package.json").exists():
        return repo_path

    # frontend/ folder
    fe = repo_path / "frontend"
    if (fe / "package.json").exists():
        return fe

    return None


# ---------------------------------------------------------
# Pre-flight validator
# ---------------------------------------------------------
def preflight_validate(repo_path: Path) -> Tuple[bool, str]:
    backend_sln = detect_backend(repo_path)
    frontend_root = detect_frontend(repo_path)

    # -----------------------------------------------------
    # Case 1: Backend only
    # -----------------------------------------------------
    if backend_sln and not frontend_root:
        return validate_backend_only(repo_path, backend_sln)

    # -----------------------------------------------------
    # Case 2: Frontend only
    # -----------------------------------------------------
    if frontend_root and not backend_sln:
        return validate_frontend_only(frontend_root)

    # -----------------------------------------------------
    # Case 3: Fullstack
    # -----------------------------------------------------
    if backend_sln and frontend_root:
        ok, msg = validate_backend_only(repo_path, backend_sln)
        if not ok:
            return False, msg

        ok, msg = validate_frontend_only(frontend_root)
        if not ok:
            return False, msg

        return True, "Pre-flight checks passed (fullstack)"

    # -----------------------------------------------------
    # Case 4: Unknown
    # -----------------------------------------------------
    return fail("Could not detect backend (.sln/.slnx) or frontend (package.json)")


# ---------------------------------------------------------
# Backend validation
# ---------------------------------------------------------
def validate_backend_only(repo_path: Path, sln: Path) -> Tuple[bool, str]:
    # Build
    ok, output = run(["dotnet", "build", str(sln), "--no-restore", "--nologo"], repo_path)
    if not ok:
        return fail(f"Backend build failed:\n{output}")

    # Test
    ok, output = run(["dotnet", "test", str(sln), "--no-build", "--nologo"], repo_path)
    if not ok:
        return fail(f"Backend tests failed:\n{output}")

    return True, "Backend pre-flight passed"


# ---------------------------------------------------------
# Frontend validation
# ---------------------------------------------------------
def validate_frontend_only(frontend_root: Path) -> Tuple[bool, str]:
    # Install dependencies (fast)
    ok, output = run(["npm", "install", "--ignore-scripts"], frontend_root)
    if not ok:
        return fail(f"Frontend dependency install failed:\n{output}")

    # Build
    ok, output = run(["npm", "run", "build"], frontend_root)
    if not ok:
        return fail(f"Frontend build failed:\n{output}")

    # Test (optional but recommended)
    ok, output = run(["npm", "test", "--", "--watch=false"], frontend_root)
    if not ok:
        return fail(f"Frontend tests failed:\n{output}")

    return True, "Frontend pre-flight passed"
