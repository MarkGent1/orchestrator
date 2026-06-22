from pathlib import Path


class CleanArchitectureEnforcer:
    """
    Enforces module boundaries for backend repositories.

    Rules:
      ✔ Anything inside tests/ is allowed
      ✔ Root-level files (Program.cs, .sln, docker-compose, etc.) are allowed
      ✔ Inside src/, only existing modules may be modified
      ✔ Anything inside a module is allowed (any folder structure)
      ✖ No new modules may be created
      ✖ No writes outside src/ except tests + root files
    """

    def __init__(self, workspace_root: Path, repo_type: str, debug: bool = False):
        self.workspace_root = workspace_root
        self.repo_type = repo_type
        self.debug = debug
        self.modules = self._discover_modules()

    # ---------------------------------------------------------
    # Module discovery (filesystem only for module roots)
    # ---------------------------------------------------------
    def _discover_modules(self):
        src = self.workspace_root / "src"
        if not src.exists():
            return []

        modules = []
        for child in src.iterdir():
            if child.is_dir():
                # Case-insensitive .csproj detection
                if any(f.suffix.lower() == ".csproj" for f in child.iterdir()):
                    modules.append(child.name)

        return modules
    
    def describe_modules(self):
        if not self.modules:
            return "(No modules detected)"
        return "\n".join(f"- {m}" for m in self.modules)

    # ---------------------------------------------------------
    # Debug helper
    # ---------------------------------------------------------
    def _debug(self, message: str):
        if self.debug:
            print(f"[ENFORCER] {message}")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def validate_path(self, rel_path: str) -> bool:
        rel_path = rel_path.replace("\\", "/")
        self._debug(f"Validating: {rel_path}")

        # 1. Allow anything inside tests/
        if rel_path.startswith("tests/"):
            self._debug("Allowed: inside tests/")
            return True

        # 2. Allow root-level files
        if self._is_root_allowed(rel_path):
            self._debug("Allowed: root-level file")
            return True

        # 3. Enforce module boundaries ONLY inside src/
        if rel_path.startswith("src/"):
            return self._validate_src_path(rel_path)

        # 4. Block everything else
        self._debug("Blocked: outside src/ and tests/")
        return False

    # ---------------------------------------------------------
    # Root-level allowances
    # ---------------------------------------------------------
    def _is_root_allowed(self, rel_path: str) -> bool:
        allowed_prefixes = [
            "Program.cs",
            "launchSettings.json",
            "docker-compose",
            ".dockerignore",
            ".gitignore",
        ]

        allowed_extensions = {".sln", ".slnx"}

        if any(rel_path.startswith(prefix) for prefix in allowed_prefixes):
            return True

        if any(rel_path.endswith(ext) for ext in allowed_extensions):
            return True

        return False

    # ---------------------------------------------------------
    # src/ enforcement
    # ---------------------------------------------------------
    def _validate_src_path(self, rel_path: str) -> bool:
        parts = rel_path.split("/")
        _, module_name, *rest = parts

        if module_name not in self.modules:
            self._debug(f"Blocked: module '{module_name}' does not exist")
            return False

        self._debug(f"Allowed: inside module '{module_name}'")
        return True
