from pathlib import Path

def find_modules(src_root: Path) -> list[str]:
    """
    A module is any folder directly under src/ that contains a .csproj file.
    """
    modules = []
    for child in src_root.iterdir():
        if child.is_dir() and any(child.glob("*.csproj")):
            modules.append(child.name)
    return modules
