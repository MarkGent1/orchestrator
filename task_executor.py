from opencode.prompt_builder import build_opencode_prompt_for_task
from opencode.client import call_opencode
from utils.path_normalization import normalize_path_casing
from architecture.enforcement import CleanArchitectureEnforcer
from utils.path_unifier import unify_path


async def execute_subtask(
    repo_path,
    workspace_path,
    work_item_id,
    work_item_title,
    task,
    subtask,
    repo_type: str,
    enforcer: CleanArchitectureEnforcer
):
    print("DEBUG: prompt_builder repo_path =", workspace_path)
    print("DEBUG: exists =", workspace_path.exists())
    print("DEBUG: children =", list(workspace_path.iterdir()))

    # ---------------------------------------------------------
    # Build the prompt for OpenCode (MUST use temp workspace)
    # ---------------------------------------------------------
    prompt = await build_opencode_prompt_for_task(
        repo_path=workspace_path,
        work_item_id=work_item_id,
        work_item_title=work_item_title,
        task=subtask,
        repo_type=repo_type,
        enforcer=enforcer,
    )

    # ---------------------------------------------------------
    # Call OpenCode to get file edits
    # ---------------------------------------------------------
    file_edits = await call_opencode(prompt)
    changed_files = []

    # ---------------------------------------------------------
    # Apply edits to TEMP workspace
    # ---------------------------------------------------------
    for edit in file_edits:
        path = (
            edit.get("path")
            or edit.get("file")
            or edit.get("file_path")
            or edit.get("new_file")
            or edit.get("filename")
        )

        if not path:
            raise ValueError(f"OpenCode edit has no path-like field: {edit}")

        # -----------------------------------------------------
        # NORMALISE RAW PATH BEFORE ANY VALIDATION
        # -----------------------------------------------------
        normalized_raw_path = unify_path(path)

        # First validation: raw path
        if not enforcer.validate_path(normalized_raw_path):
            raise ValueError(f"Illegal raw path from OpenCode: {normalized_raw_path}")

        # -----------------------------------------------------
        # Normalize casing and folder names
        # -----------------------------------------------------
        rel_path = normalize_path_casing(
            normalized_raw_path,
            repo_type,
            workspace_root=workspace_path
        )

        # Second validation: normalized path
        if repo_type == "backend":
            if not enforcer.validate_path(rel_path):
                raise ValueError(
                    f"Illegal path generated under Clean Architecture rules: {rel_path}"
                )

        # -----------------------------------------------------
        # Write file to workspace
        # -----------------------------------------------------
        content = edit.get("content", "")

        full_path = workspace_path / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        changed_files.append({
            "path": rel_path,
            "content": content
        })

    return changed_files
