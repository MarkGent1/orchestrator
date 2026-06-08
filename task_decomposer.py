from opencode_client import call_opencode

async def decompose_task(work_item_id, work_item_title, task):
    prompt = f"""
You are an expert software architect.

Decompose the following task into 2–6 smaller sub-tasks.

Work Item {work_item_id}: {work_item_title}

Task:
{task['title']}
{task.get('description', '')}

Return ONLY JSON:
[
  {{"title": "...", "description": "..."}},
  ...
]
"""
    return await call_opencode(prompt)
