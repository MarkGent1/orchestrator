from __future__ import annotations
from typing import Any, Dict

from agents.base.agent import Agent, AgentResult, ContextPacket, ModelProfile, ContextProfile, ReliabilityProfile
from work_item_planning import WorkItemPlanner


class PlanningAgent(Agent):
    """
    Wraps WorkItemPlanner.plan_work_item(work_item_id).
    Expects:
      context.task_ctx["work_item_id"]
    """

    def __init__(self, planner: WorkItemPlanner, model_name: str):
        super().__init__(
            name="PlanningAgent",
            role="plan_work_item",
            model_profile=ModelProfile(name=model_name),
            context_profile=ContextProfile(required_layers=["task"]),
            reliability_profile=ReliabilityProfile(retries=1),
        )
        self.planner = planner

    async def _execute(self, context: ContextPacket) -> AgentResult:
        work_item_id: int = context.task_ctx["work_item_id"]

        result: Dict[str, Any] = await self.planner.plan_work_item(work_item_id)

        return AgentResult(
            success=True,
            payload=result,
        )
