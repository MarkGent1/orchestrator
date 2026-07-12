from __future__ import annotations
from typing import Any, Tuple

from agents.base.agent import Agent, AgentResult, ContextPacket, ModelProfile, ContextProfile, ReliabilityProfile
from agents.base.agent_result import AgentError
from validator import BuildTestValidator


class ValidationAgent(Agent):
    """
    Wraps BuildTestValidator.run_validation().
    Expects:
      context.task_ctx["validator"] -> BuildTestValidator instance
    """

    def __init__(self, model_name: str):
        super().__init__(
            name="ValidationAgent",
            role="run_validation",
            model_profile=ModelProfile(name=model_name),
            context_profile=ContextProfile(required_layers=["task"]),
            reliability_profile=ReliabilityProfile(retries=1),
        )

    async def _execute(self, context: ContextPacket) -> AgentResult:
        validator: BuildTestValidator = context.task_ctx["validator"]

        ok, message = await validator.run_validation()

        return AgentResult(
            success=ok,
            payload={"message": message},
            error=None if ok else AgentError(type="validation_error", message=message),
        )
