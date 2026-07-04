import re
from typing import Dict, Any, List, Optional
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
        # Idempotency guard: if this Work Item already has child
        # tasks from a previous orchestrator run (e.g. the run
        # crashed after planning but before finishing, and got
        # re-invoked), reuse that existing plan instead of asking the
        # model again and creating a second, duplicate set of child
        # tasks and a duplicate "plan generated" comment every retry.
        # -----------------------------------------------------
        existing_tasks = await self._get_existing_child_tasks(wi)

        if existing_tasks:
            print(
                f"Work Item {work_item_id} already has {len(existing_tasks)} "
                f"child task(s) -- reusing the existing plan instead of "
                f"generating a new one."
            )
            plan = {"title": title, "tasks": existing_tasks}
            return {
                "plan": plan,
                "created_tasks": [],
                "quality_issues": quality_issues,
            }

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
    {{ "title": "...", "description": "..." }},
    ...
  ]
"""

        plan_tasks = await call_model_json(prompt, model, provider)

        # Match the same defensive guard used in task_decomposer.py:
        # if the model returns something other than a JSON array (e.g.
        # a dict, or malformed output that slipped past the JSON
        # pipeline), fail with a clear, actionable error here instead
        # of letting `task["title"]` below raise a confusing KeyError/
        # TypeError several lines later.
        if not isinstance(plan_tasks, list):
            raise ValueError(
                f"Expected a JSON array of tasks from the planning model, got: {type(plan_tasks)}"
            )

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
    # Idempotency helper
    # ---------------------------------------------------------
    async def _get_existing_child_tasks(self, wi: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Looks for work items already linked as "child" relations on
        this Work Item (the standard Azure DevOps REST API shape:
        wi["relations"] entries with rel ==
        "System.LinkTypes.Hierarchy-Forward", whose "url" ends in the
        child work item's numeric id). If any are found, we assume a
        previous orchestrator run already planned and created them.

        NOTE: this depends on the ADO MCP server's getWorkItem
        response including "relations" in this shape. If the server
        doesn't return relations at all, `wi.get("relations")` is
        just empty/missing, this returns [], and planning proceeds
        exactly as it did before this check existed -- it fails open
        rather than breaking planning if that assumption turns out to
        be wrong for your server implementation.
        """
        relations = wi.get("relations") or []
        child_ids = []

        for rel in relations:
            if rel.get("rel") != "System.LinkTypes.Hierarchy-Forward":
                continue
            match = re.search(r"/(\d+)$", rel.get("url", ""))
            if match:
                child_ids.append(int(match.group(1)))

        if not child_ids:
            return []

        existing_tasks = []
        for child_id in child_ids:
            try:
                child = await self.ado.get_work_item(child_id)
            except Exception as ex:
                # A stale/broken link shouldn't block resuming on the
                # rest of a legitimate existing plan.
                print(f"Could not fetch child Work Item {child_id}, skipping it: {ex}")
                continue

            existing_tasks.append({
                "title": child["fields"].get("System.Title", ""),
                "description": child["fields"].get("System.Description", ""),
            })

        return existing_tasks

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
