from typing import Dict, Any, List
from model_selector import select_model_for_planning, call_model_json

class WorkItemPlanner:
    """
    Generates a clean, non-overlapping SDLC task plan for an Azure DevOps Work Item,
    validates quality, creates child tasks, posts a plan comment, and transitions
    the Work Item to Active.
    """

    def __init__(self, ado_mcp_client, model_config):
        self.ado = ado_mcp_client
        self.model_config = model_config

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    async def plan_work_item(self, work_item_id: int) -> Dict[str, Any]:
        wi = await self.ado.get_work_item(work_item_id)

        title = wi["fields"].get("System.Title", "").strip()
        description = wi["fields"].get("System.Description", "").strip()
        acceptance = wi["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria", "").strip()

        quality_issues = self.validate_work_item(title, description, acceptance)

        # -----------------------------------------------------
        # AI-Generated Task Plan
        # -----------------------------------------------------
        model, provider = select_model_for_planning(self.model_config)

        prompt = f"""
Generate a minimal, non-overlapping SDLC task plan for this Work Item.

Title: {title}
Description: {description}
Acceptance Criteria: {acceptance}

Rules:
- Only generate tasks required for THIS Work Item.
- No documentation, ADRs, or unrelated features.
- Keep tasks minimal and focused.
- Return ONLY a JSON array of subtasks:
  [
    {"title": "...", "description": "..."},
    ...
  ]
"""

        plan_tasks = await call_model_json(prompt, model, provider)

        plan = {
            "title": title,
            "tasks": plan_tasks
        }

        # -----------------------------------------------------
        # Create child tasks in Azure DevOps
        # -----------------------------------------------------
        created_tasks: List[Dict[str, Any]] = []
        for task in plan["tasks"]:
            created = await self.ado.create_child_task(
                parent_id=work_item_id,
                title=task["title"],
                description=task["description"],
            )
            created_tasks.append(created)

        await self.ado.add_comment(
            work_item_id,
            self.render_plan_comment(plan, created_tasks, quality_issues),
        )

        await self.ado.update_work_item_state(work_item_id, "Active")

        return {
            "plan": plan,
            "created_tasks": created_tasks,
            "quality_issues": quality_issues,
        }

    # ---------------------------------------------------------
    # Quality validation
    # ---------------------------------------------------------
    def validate_work_item(self, title: str, description: str, acceptance: str) -> List[str]:
        issues = []

        if len(title) < 5:
            issues.append("Title is too short.")

        if not description or len(description) < 20:
            issues.append("Description is missing or too short.")

        if not acceptance:
            issues.append("Acceptance Criteria missing.")

        if "As a" not in description and "as a" not in description and "I want" not in description:
            issues.append("User story format missing.")

        return issues

    # ---------------------------------------------------------
    # Comment rendering
    # ---------------------------------------------------------
    def render_plan_comment(
        self,
        plan: Dict[str, Any],
        created_tasks: List[Dict[str, Any]],
        issues: List[str],
    ) -> str:
        comment = "### 🧠 Work Item Plan Generated\n\n"

        if issues:
            comment += "#### ⚠️ Quality Issues Detected\n"
            for issue in issues:
                comment += f"- {issue}\n"
            comment += "\n"

        comment += "#### 📋 Task Plan\n"
        for t in plan["tasks"]:
            comment += f"- **{t['title']}** — {t['description']}\n"

        comment += "\n#### 🆕 Created Tasks\n"
        for t in created_tasks:
            comment += f"- {t['id']}: {t['fields']['System.Title']}\n"

        return comment
