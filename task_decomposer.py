from opencode.client import call_opencode_json

async def decompose_task(work_item_id: int, work_item_title: str, task: dict, repo_type: str):
    prompt = f"""
You are OpenCode — an AI software engineer.

Decompose the following task into 2–6 clear, actionable subtasks.

### Work Item
{work_item_title}

### Task
{task['title']}
{task.get('description', '')}

### Repository Type
{repo_type}

### CRITICAL RULES
- If backend: generate ONLY C#/.NET subtasks.
- If frontend: generate ONLY TypeScript/React subtasks.
- Do NOT generate subtasks for the wrong language.
- Do NOT mention NestJS, Node.js, Java, Python, or unrelated stacks.

### Output Format (MANDATORY)
Return ONLY a JSON array of subtasks.
Each subtask must contain:
- "title"
- "description"

Return [] if no subtasks are needed.
"""

    subtasks = await call_opencode_json(prompt)

    if not isinstance(subtasks, list):
        return []

    return subtasks
