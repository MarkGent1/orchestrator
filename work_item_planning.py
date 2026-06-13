from typing import Dict, Any, List


class WorkItemPlanner:
    """
    Generates a task plan for an Azure DevOps Work Item, validates quality,
    creates child tasks, posts a plan comment, and transitions the Work Item
    to Active.

    This class is intentionally deterministic: the same Work Item always
    produces the same plan structure.
    """

    def __init__(self, ado_mcp_client):
        self.ado = ado_mcp_client

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    async def plan_work_item(self, work_item_id: int) -> Dict[str, Any]:
        """
        Fetch the Work Item, validate quality, generate a task plan,
        create child tasks, post a comment, and update state.
        """
        wi = await self.ado.get_work_item(work_item_id)

        title = wi["fields"].get("System.Title", "").strip()
        description = wi["fields"].get("System.Description", "").strip()
        acceptance = wi["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria", "").strip()

        quality_issues = self.validate_work_item(title, description, acceptance)
        plan = self.generate_task_plan(title, description, acceptance)

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
        """
        Basic Work Item quality checks.
        """
        issues = []

        if len(title) < 5:
            issues.append("Title is too short.")

        if not description or len(description) < 20:
            issues.append("Description is missing or too short.")

        if not acceptance:
            issues.append("Acceptance Criteria missing.")

        if "As a" not in description and "I want" not in description:
            issues.append("User story format missing.")

        return issues

    # ---------------------------------------------------------
    # Task plan generation
    # ---------------------------------------------------------
    def generate_task_plan(self, title: str, description: str, acceptance: str) -> Dict[str, Any]:
        """
        Deterministic task plan for the orchestrator.
        """
        return {
            "title": title,
            "tasks": [
                {
                    "title": f"Analyse Work Item: {title}",
                    "description": "Review the Work Item, acceptance criteria, and dependencies.",
                },
                {
                    "title": "Design solution",
                    "description": "Define data structures, API changes, and architecture impacts.",
                },
                {
                    "title": "Implement backend changes",
                    "description": "Write code, update models, add business logic.",
                },
                {
                    "title": "Implement frontend changes",
                    "description": "Update UI components, forms, and validation.",
                },
                {
                    "title": "Write automated tests",
                    "description": "Unit tests, integration tests, and acceptance tests.",
                },
                {
                    "title": "Update documentation",
                    "description": "Update README, ADRs, and API docs.",
                },
            ],
        }

    # ---------------------------------------------------------
    # Comment rendering
    # ---------------------------------------------------------
    def render_plan_comment(
        self,
        plan: Dict[str, Any],
        created_tasks: List[Dict[str, Any]],
        issues: List[str],
    ) -> str:
        """
        Render a markdown comment summarising the plan, quality issues,
        and created tasks.
        """
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
