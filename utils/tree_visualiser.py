from pathlib import Path

def print_tree(root: Path, max_depth: int = 4, prefix: str = ""):
    def _walk(path: Path, depth: int, prefix: str):
        if depth > max_depth:
            return

        entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            print(prefix + connector + entry.name)

            if entry.is_dir():
                new_prefix = prefix + ("    " if is_last else "│   ")
                _walk(entry, depth + 1, new_prefix)

    print(root.name)
    _walk(root, 0, "")
