def build_pr_description(plan, task_memory, build_logs):
    return f"""
# Work Item {plan['id']}: {plan['title']}

## Plan Summary
{chr(10).join(f"- {t['title']}" for t in plan['tasks'])}

{task_memory.to_markdown()}

## Build & Test Logs
{build_logs}
"""
