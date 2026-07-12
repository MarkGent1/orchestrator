from __future__ import annotations

from agents.base.agent import (
    Agent,
    AgentResult,
    AgentError,
    ContextPacket,
    ModelProfile,
    ContextProfile,
    ReliabilityProfile,
)

from architecture.enforcement import CleanArchitectureEnforcer


class ArchitectureAgent(Agent):
    """
    Wraps CleanArchitectureEnforcer for:
      - module discovery
      - module description
      - path validation

    Expects:
      context.task_ctx["enforcer"] -> CleanArchitectureEnforcer
      context.micro_ctx["path"]    -> str (optional)
    """

    def __init__(self, model_name: str = "architecture-agent"):
        super().__init__(
            name="ArchitectureAgent",
            role="architecture_validation",
            model_profile=ModelProfile(name=model_name),
            context_profile=ContextProfile(
                required_layers=["task"],   # micro optional
                forbidden_layers=[]
            ),
            reliability_profile=ReliabilityProfile(retries=1),
        )

    async def _execute(self, context: ContextPacket) -> AgentResult:
        enforcer: CleanArchitectureEnforcer = context.task_ctx["enforcer"]

        # If a specific path is provided, validate it
        if context.micro_ctx and "path" in context.micro_ctx:
            rel_path = context.micro_ctx["path"]
            ok = enforcer.validate_path(rel_path)

            if ok:
                return AgentResult(
                    success=True,
                    payload={
                        "path": rel_path,
                        "valid": True,
                        "modules": enforcer.modules,
                        "description": enforcer.describe_modules(),
                    },
                )
            else:
                return AgentResult(
                    success=False,
                    error=AgentError(
                        type="architecture_error",
                        message=f"Illegal path under Clean Architecture rules: {rel_path}",
                        details={"modules": enforcer.modules},
                    ),
                )

        # Otherwise return module description
        return AgentResult(
            success=True,
            payload={
                "modules": enforcer.modules,
                "description": enforcer.describe_modules(),
            },
        )
