from opencode_prompt_builder import build_opencode_prompt_for_task
from file_editing import apply_file_edits_for_task
from opencode_client import call_opencode

async def execute_subtask(repo_path, work_item_id, work_item_title, task, subtask):
    prompt = await build_opencode_prompt_for_task(
        repo_path=repo_path,
        work_item_id=work_item_id,
        work_item_title=work_item_title,
        task=subtask,
    )

    file_edits = await call_opencode(prompt)
    changed_files = apply_file_edits_for_task(repo_path, file_edits)
    return changed_files
