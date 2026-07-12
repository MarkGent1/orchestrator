from __future__ import annotations
from typing import Optional

from agents.base.agent_result import AgentError, AgentResult
from agents.base.context_packet import ContextPacket
from agents.base.context_profile import ContextProfile
from agents.base.model_profile import ModelProfile
from agents.base.reliability_profile import ReliabilityProfile

# ============================================================
# Agent Base Class
# ============================================================

class Agent:
    """
    Base class for all agents.
    Subclasses implement `async _execute()`.
    """

    def __init__(
        self,
        name: str,
        role: str,
        model_profile: ModelProfile,
        context_profile: ContextProfile,
        reliability_profile: ReliabilityProfile,
    ):
        self.name = name
        self.role = role
        self.model_profile = model_profile
        self.context_profile = context_profile
        self.reliability_profile = reliability_profile

    async def run(self, context: ContextPacket) -> AgentResult:
        self._validate_context(context)
        self._log_start(context)
        result = await self._execute_with_reliability(context)
        self._log_end(result)
        return result

    async def _execute_with_reliability(self, context: ContextPacket) -> AgentResult:
        retries = max(1, self.reliability_profile.retries)
        last_error: Optional[AgentError] = None

        for attempt in range(1, retries + 1):
            result = await self._execute(context)

            if result.success:
                result.metadata.update({
                    "agent_name": self.name,
                    "agent_role": self.role,
                    "attempt": attempt,
                    "model": self.model_profile.name,
                })
                return result

            last_error = result.error or AgentError(
                type="unknown_error",
                message=f"{self.name} failed without error details",
            )

        return AgentResult(
            success=False,
            error=last_error,
            metadata={
                "agent_name": self.name,
                "agent_role": self.role,
                "attempts": retries,
                "model": self.model_profile.name,
            },
        )

    async def _execute(self, context: ContextPacket) -> AgentResult:
        raise NotImplementedError(f"{self.__class__.__name__} must implement _execute()")

    def _validate_context(self, context: ContextPacket):
        present = set(context.layer_names())
        required = set(self.context_profile.required_layers)
        forbidden = set(self.context_profile.forbidden_layers)

        missing = required - present
        if missing:
            raise ValueError(
                f"Agent '{self.name}' missing required context layers: {sorted(missing)}"
            )

        illegal = present & forbidden
        if illegal:
            raise ValueError(
                f"Agent '{self.name}' received forbidden context layers: {sorted(illegal)}"
            )

    def _log_start(self, context: ContextPacket):
        pass

    def _log_end(self, result: AgentResult):
        pass
