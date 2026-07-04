from prompt_builder import build_opencode_prompt_for_task
from model_selector import select_model_for_task_execution, call_model
from architecture.enforcement import CleanArchitectureEnforcer
from file_editing import apply_file_edits_for_task


async def execute_subtask(
    repo_path,
    workspace_path,
    work_item_id,
    work_item_title,
    task,
    subtask,
    repo_type: str,
    enforcer: CleanArchitectureEnforcer,
    model_config: object
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
    # ⭐ Select model dynamically (Claude or OpenAI)
    # ---------------------------------------------------------
    model, provider = select_model_for_task_execution(
        subtask["title"],
        repo_type,
        model_config
    )

    # ---------------------------------------------------------
    # ⭐ Call selected model (Claude or OpenAI)
    # ---------------------------------------------------------
    file_edits = await call_model(prompt, model, provider)

    # ---------------------------------------------------------
    # Apply edits to TEMP workspace.
    #
    # This routes through the same apply_file_edits_for_task() used by
    # the FixLoop retry path (see validator.py), so "create"/"modify"/
    # "delete" are handled identically everywhere instead of this
    # execution path carrying its own separate, less complete copy of
    # the logic. Notably, the previous inline version here never
    # looked at "instructions" at all -- a model-issued "delete" would
    # have silently overwritten the file with (likely empty) content
    # instead of removing it.
    # ---------------------------------------------------------
    changed_files = apply_file_edits_for_task(
        workspace_path,
        file_edits,
        repo_type,
        enforcer=enforcer,
    )

    return changed_files
