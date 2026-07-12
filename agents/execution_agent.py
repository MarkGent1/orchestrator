from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path

from agents.base.agent import Agent, AgentResult, ContextPacket, ModelProfile, ContextProfile, ReliabilityProfile
from task_executor import execute_subtask
from architecture.enforcement import CleanArchitectureEnforcer


class ExecutionAgent(Agent):
    """
    Wraps execute_subtask(...).
    Expects in context.task_ctx:
      - "repo_path" (Path)
      - "workspace_path" (Path)
      - "work_item_id" (int)
      - "work_item_title" (str)
      - "task" (dict)
      - "subtask" (dict)
      - "repo_type" (str)
      - "enforcer" (CleanArchitectureEnforcer)
      - "model_config" (object)
    """

    def __init__(self, model_name: str):
        super().__init__(
            name="ExecutionAgent",
            role="execute_subtask",
            model_profile=ModelProfile(name=model_name),
            context_profile=ContextProfile(required_layers=["task"]),
            reliability_profile=ReliabilityProfile(retries=1),
        )

    async def _execute(self, context: ContextPacket) -> AgentResult:
        tc = context.task_ctx

        changed_files: List[Dict[str, Any]] = await execute_subtask(
            repo_path=tc["repo_path"],
            workspace_path=tc["workspace_path"],
            work_item_id=tc["work_item_id"],
            work_item_title=tc["work_item_title"],
            task=tc["task"],
            subtask=tc["subtask"],
            repo_type=tc["repo_type"],
            enforcer=tc["enforcer"],
            model_config=tc["model_config"],
        )

        return AgentResult(
            success=True,
            payload=changed_files,
        )
