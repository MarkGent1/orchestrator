from __future__ import annotations
from typing import Any, Dict

from agents.base.agent import Agent, AgentResult, ContextPacket, ModelProfile, ContextProfile, ReliabilityProfile
from pr_enhancer import build_pr_description
from task_memory import TaskMemory


class PRAgent(Agent):
    """
    Wraps build_pr_description(plan, task_memory, build_logs).
    Expects in context.task_ctx:
      - "plan" (dict)
      - "task_memory" (TaskMemory)
      - "build_logs" (str)
    """

    def __init__(self, model_name: str = "pr-agent"):
        super().__init__(
            name="PRAgent",
            role="build_pr_description",
            model_profile=ModelProfile(name=model_name),
            context_profile=ContextProfile(required_layers=["task"]),
            reliability_profile=ReliabilityProfile(retries=1),
        )

    async def _execute(self, context: ContextPacket) -> AgentResult:
        tc = context.task_ctx

        plan: Dict[str, Any] = tc["plan"]
        task_memory: TaskMemory = tc["task_memory"]
        build_logs: str = tc["build_logs"]

        pr_body = build_pr_description(plan, task_memory, build_logs)

        return AgentResult(
            success=True,
            payload={"pr_body": pr_body},
        )
