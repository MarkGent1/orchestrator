from __future__ import annotations
from typing import Any, Dict, List

from agents.base.agent import Agent, AgentResult, ContextPacket, ModelProfile, ContextProfile, ReliabilityProfile
from task_decomposer import decompose_task


class DecompositionAgent(Agent):
    """
    Wraps decompose_task(...).
    Expects in context.task_ctx:
      - "work_item_id"
      - "work_item_title"
      - "task"
      - "repo_type"
      - "model_config"
    """

    def __init__(self, model_name: str):
        super().__init__(
            name="DecompositionAgent",
            role="decompose_task",
            model_profile=ModelProfile(name=model_name),
            context_profile=ContextProfile(required_layers=["task"]),
            reliability_profile=ReliabilityProfile(retries=1),
        )

    async def _execute(self, context: ContextPacket) -> AgentResult:
        tc = context.task_ctx

        subtasks: List[Dict[str, Any]] = await decompose_task(
            work_item_id=tc["work_item_id"],
            work_item_title=tc["work_item_title"],
            task=tc["task"],
            repo_type=tc["repo_type"],
            model_config=tc["model_config"],
        )

        return AgentResult(
            success=True,
            payload=subtasks,
        )
