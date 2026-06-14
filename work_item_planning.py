from typing import Dict, Any, List


class WorkItemPlanner:
    """
    Generates a clean, non-overlapping SDLC task plan for an Azure DevOps Work Item,
    validates quality, creates child tasks, posts a plan comment, and transitions
    the Work Item to Active.
    """

    def __init__(self, ado_mcp_client):
        self.ado = ado_mcp_client

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    async def plan_work_item(self, work_item_id: int) -> Dict[str, Any]:
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
    # Task plan generation (non-overlapping)
    # ---------------------------------------------------------
    def generate_task_plan(self, title: str, description: str, acceptance: str) -> Dict[str, Any]:
        text = f"{title} {description} {acceptance}".lower()

        is_frontend = any(word in text for word in [
            "reactjs", "nextjs", "frontend"
        ])

        if is_frontend:
            tasks = [
                {
                    "title": "Implement frontend changes",
                    "description": (
                        "Implement only the frontend code required for this Work Item. "
                        "Focus strictly on components, forms, validation, and API calls. "
                        "Do not generate documentation or unrelated features."
                    ),
                },
                {
                    "title": "Write automated tests",
                    "description": (
                        "Write only the tests required for the new frontend code. "
                        "Use minimal, focused test cases."
                    ),
                },
                {
                    "title": "Refactor and finalise",
                    "description": (
                        "Perform minimal cleanup and ensure the frontend build and tests pass."
                    ),
                },
            ]
        else:
            tasks = [
                {
                    "title": "Implement backend changes",
                    "description": (
                        "Implement only the backend code required for this Work Item. "
                        "Focus strictly on controllers, services, models, and logic. "
                        "Do not generate documentation, ADRs, or unrelated features."
                    ),
                },
                {
                    "title": "Write automated tests",
                    "description": (
                        "Write only the tests required for the new backend code. "
                        "Keep tests minimal and focused."
                    ),
                },
                {
                    "title": "Refactor and finalise",
                    "description": (
                        "Perform minimal cleanup and ensure the backend build and tests pass."
                    ),
                },
            ]

        return {
            "title": title,
            "tasks": tasks,
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
