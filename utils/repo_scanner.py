from pathlib import Path

def build_module_map(src_root: Path) -> dict:
    """
    Returns:
    {
      "ModuleName": {
        "path": Path,
        "projects": [Path],
        "folders": [str]
      },
      ...
    }
    """
    module_map = {}

    for child in src_root.iterdir():
        if not child.is_dir():
            continue

        projects = list(child.glob("*.csproj"))
        if not projects:
            continue

        folders = [p.name for p in child.iterdir() if p.is_dir()]

        module_map[child.name] = {
            "path": child,
            "projects": projects,
            "folders": folders,
        }

    return module_map
