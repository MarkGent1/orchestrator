from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import json
import os


@dataclass
class SubtaskState:
    title: str
    done: bool = False
    error: Optional[Dict[str, Any]] = None


@dataclass
class TaskState:
    title: str
    subtasks: List[SubtaskState] = field(default_factory=list)


@dataclass
class PlanState:
    title: str
    tasks: List[TaskState]


class RunState:
    """
    Minimal persistence layer for Phase 2.
    Stores plan, tasks, subtasks, validation, PR URL.
    """

    def __init__(self, repo_path: str, work_item_id: str):
        self.repo_path = repo_path
        self.work_item_id = work_item_id
        self.plan: Optional[PlanState] = None
        self.validated: bool = False
        self.pr_url: Optional[str] = None

    # ---------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------

    @staticmethod
    def _path(repo_path: str, work_item_id: str) -> str:
        return os.path.join(repo_path, ".orchestrator", f"{work_item_id}.json")

    @classmethod
    def load(cls, repo_path: str, work_item_id: str) -> Optional["RunState"]:
        path = cls._path(repo_path, work_item_id)
        if not os.path.exists(path):
            return None

        with open(path, "r") as f:
            data = json.load(f)

        rs = cls(repo_path, work_item_id)
        rs.plan = PlanState(
            title=data["plan"]["title"],
            tasks=[
                TaskState(
                    title=t["title"],
                    subtasks=[SubtaskState(**s) for s in t["subtasks"]],
                )
                for t in data["plan"]["tasks"]
            ],
        )
        rs.validated = data.get("validated", False)
        rs.pr_url = data.get("pr_url")
        return rs

    @classmethod
    def new(cls, repo_path: str, work_item_id: str) -> "RunState":
        return cls(repo_path, work_item_id)

    def save(self):
        path = self._path(self.repo_path, self.work_item_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        data = {
            "plan": {
                "title": self.plan.title if self.plan else None,
                "tasks": [
                    {
                        "title": t.title,
                        "subtasks": [
                            {"title": s.title, "done": s.done, "error": s.error}
                            for s in t.subtasks
                        ],
                    }
                    for t in (self.plan.tasks if self.plan else [])
                ],
            },
            "validated": self.validated,
            "pr_url": self.pr_url,
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    # ---------------------------------------------------------
    # Plan helpers
    # ---------------------------------------------------------

    def plan_exists(self) -> bool:
        return self.plan is not None

    def save_plan(self, plan_payload: Dict[str, Any]):
        self.plan = PlanState(
            title=plan_payload["title"],
            tasks=[TaskState(title=t["title"]) for t in plan_payload["tasks"]],
        )
        self.save()

    # ---------------------------------------------------------
    # Subtask helpers
    # ---------------------------------------------------------

    def has_subtasks(self, task: TaskState) -> bool:
        return len(task.subtasks) > 0

    def save_subtasks(self, task: TaskState, subtasks_payload: List[Dict[str, Any]]):
        task.subtasks = [SubtaskState(title=s["title"]) for s in subtasks_payload]
        self.save()

    def get_subtasks(self, task: TaskState) -> List[SubtaskState]:
        return task.subtasks

    def mark_subtask_done(self, task: TaskState, subtask: SubtaskState):
        subtask.done = True
        subtask.error = None
        self.save()

    def mark_failed(self, task: Optional[TaskState], subtask: Optional[SubtaskState], failure_type: Any):
        if subtask:
            subtask.error = {"type": failure_type.type, "message": failure_type.message}
        self.save()

    # ---------------------------------------------------------
    # Validation + PR
    # ---------------------------------------------------------

    def mark_validated(self):
        self.validated = True
        self.save()

    def pr_exists(self) -> bool:
        return self.pr_url is not None

    def save_pr_url(self, url: str):
        self.pr_url = url
        self.save()
