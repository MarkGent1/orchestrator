from __future__ import annotations
from typing import Any, Dict, List

from agents.base.agent import Agent, AgentResult, ContextPacket, ModelProfile, ContextProfile, ReliabilityProfile
from fix_loop import FixLoop


class FixLoopAgent(Agent):
    """
    Wraps FixLoop.attempt_fix(error_output).
    Expects:
      context.task_ctx["fix_loop"]  -> FixLoop instance
      context.micro_ctx["error_output"] -> str
    """

    def __init__(self, model_name: str):
        super().__init__(
            name="FixLoopAgent",
            role="attempt_fix",
            model_profile=ModelProfile(name=model_name),
            context_profile=ContextProfile(required_layers=["task", "micro"]),
            reliability_profile=ReliabilityProfile(retries=1),
        )

    async def _execute(self, context: ContextPacket) -> AgentResult:
        fix_loop: FixLoop = context.task_ctx["fix_loop"]
        error_output: str = context.micro_ctx["error_output"]

        edits: List[Dict[str, Any]] = await fix_loop.attempt_fix(error_output)

        return AgentResult(
            success=True,
            payload=edits,
        )
