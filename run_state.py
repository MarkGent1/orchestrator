import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List


# State files live under the ORCHESTRATOR's own directory, not inside
# the target repo. `.orchestrator-tmp` inside the target repo is wiped
# and recreated at the start of every run, so it can't hold anything
# that needs to survive a crash; storing state here also means nothing
# needs to be gitignored in the user's repos.
STATE_DIR = Path(__file__).parent / ".orchestrator-state"


def _safe_repo_key(repo_path: Path) -> str:
    """
    Turns an absolute repo path into a filesystem-safe key, so state
    files for different repos never collide with each other.
    """
    key = str(Path(repo_path).resolve())
    return re.sub(r"[^a-zA-Z0-9]+", "_", key).strip("_")


class RunState:
    """
    Persists orchestrator progress for a single (repo, work item) run
    to a local JSON file, so a crash partway through -- a bad model
    response, a build failure that exhausts the fix loop, a network
    blip -- doesn't force starting completely over from Work Item
    planning and Task 1 again.

    Tracks, at the finest granularity that's actually safe to trust:
      - the branch name (so it isn't recreated / re-derived)
      - the top-level task plan (title/description) and, once each
        task has been decomposed for the first time, its subtasks
      - a "done" flag per task and per subtask
      - whether build/test validation has already passed
      - the PR url, once opened

    Subtask decomposition specifically is persisted the first time
    it's computed rather than being recomputed on resume, because the
    decomposition model call is not guaranteed to return the same
    breakdown twice -- recomputing it on resume could produce subtask
    titles that don't match what was already completed, making
    "already done" checks meaningless.
    """

    def __init__(self, repo_path: Path, work_item_id: int):
        self.repo_path = Path(repo_path)
        self.work_item_id = work_item_id
        self.path = STATE_DIR / f"{_safe_repo_key(self.repo_path)}-{work_item_id}.json"

        self.branch_name: Optional[str] = None
        self.plan_title: Optional[str] = None
        self.tasks: List[Dict[str, Any]] = []
        self.validated: bool = False
        self.pr_url: Optional[str] = None

    # -----------------------------------------------------------
    # Load / save
    # -----------------------------------------------------------
    @classmethod
    def load(cls, repo_path: Path, work_item_id: int) -> Optional["RunState"]:
        """
        Returns a populated RunState if a saved run exists for this
        (repo, work item) pair, otherwise None. Never raises -- a
        corrupt or unreadable state file is treated the same as "no
        saved state" rather than crashing the orchestrator over what
        is meant to be a convenience feature.
        """
        state = cls(repo_path, work_item_id)
        if not state.path.exists():
            return None

        try:
            data = json.loads(state.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

        state.branch_name = data.get("branch_name")
        state.plan_title = data.get("plan_title")
        state.tasks = data.get("tasks", [])
        state.validated = data.get("validated", False)
        state.pr_url = data.get("pr_url")
        return state

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "work_item_id": self.work_item_id,
            "repo_path": str(self.repo_path),
            "branch_name": self.branch_name,
            "plan_title": self.plan_title,
            "tasks": self.tasks,
            "validated": self.validated,
            "pr_url": self.pr_url,
        }

        # Write atomically (write to a temp file, then rename) so a
        # crash mid-write never leaves a half-written, unparseable
        # state file behind that would silently disable resume.
        tmp_path = self.path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp_path.replace(self.path)

    def clear(self) -> None:
        """Call once the work item is fully done (PR opened and linked)."""
        if self.path.exists():
            self.path.unlink()

    # -----------------------------------------------------------
    # Plan-level helpers
    # -----------------------------------------------------------
    def init_plan(self, branch_name: str, plan_title: str, tasks: List[Dict[str, Any]]) -> None:
        self.branch_name = branch_name
        self.plan_title = plan_title
        self.tasks = [
            {
                "title": t["title"],
                "description": t.get("description", ""),
                "done": False,
                "subtasks": None,
            }
            for t in tasks
        ]
        self.save()

    def get_task(self, task_title: str) -> Optional[Dict[str, Any]]:
        for t in self.tasks:
            if t["title"] == task_title:
                return t
        return None

    def set_task_subtasks(self, task_title: str, subtasks: List[Dict[str, Any]]) -> None:
        task = self.get_task(task_title)
        if task is None:
            return
        task["subtasks"] = [
            {"title": s["title"], "description": s.get("description", ""), "done": False}
            for s in subtasks
        ]
        self.save()

    def is_subtask_done(self, task_title: str, subtask_title: str) -> bool:
        task = self.get_task(task_title)
        if not task or not task.get("subtasks"):
            return False
        for s in task["subtasks"]:
            if s["title"] == subtask_title:
                return bool(s["done"])
        return False

    def mark_subtask_done(self, task_title: str, subtask_title: str) -> None:
        task = self.get_task(task_title)
        if task is None or not task.get("subtasks"):
            return
        for s in task["subtasks"]:
            if s["title"] == subtask_title:
                s["done"] = True
                break
        if task["subtasks"] and all(s["done"] for s in task["subtasks"]):
            task["done"] = True
        self.save()

    def mark_validated(self) -> None:
        self.validated = True
        self.save()

    def mark_pr_opened(self, pr_url: str) -> None:
        self.pr_url = pr_url
        self.save()
