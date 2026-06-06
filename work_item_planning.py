class WorkItemPlanner:
    def __init__(self, ado_mcp_client):
        self.ado = ado_mcp_client

    async def plan_work_item(self, work_item_id: int):
        wi = await self.ado.get_work_item(work_item_id)

        title = wi["fields"].get("System.Title", "")
        description = wi["fields"].get("System.Description", "")
        acceptance = wi["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria", "")

        quality_issues = self.validate_work_item(title, description, acceptance)
        plan = self.generate_task_plan(title, description, acceptance)

        created_tasks = []
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

    def validate_work_item(self, title, description, acceptance):
        issues = []

        if len(title.strip()) < 5:
            issues.append("Title is too short.")

        if not description or len(description.strip()) < 20:
            issues.append("Description is missing or too short.")

        if not acceptance:
            issues.append("Acceptance Criteria missing.")

        if "As a" not in description and "I want" not in description:
            issues.append("User story format missing.")

        return issues

    def generate_task_plan(self, title, description, acceptance):
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

    def render_plan_comment(self, plan, created_tasks, issues):
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