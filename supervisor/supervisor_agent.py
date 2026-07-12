from __future__ import annotations
import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from agents.base.agent import ContextPacket
from agents.planning_agent import PlanningAgent
from agents.decomposition_agent import DecompositionAgent
from agents.execution_agent import ExecutionAgent
from agents.fixloop_agent import FixLoopAgent
from agents.validation_agent import ValidationAgent
from agents.pr_agent import PRAgent
from agents.architecture_agent import ArchitectureAgent

from run_state import RunState
from repo_type import detect_repo_type
from architecture.enforcement import CleanArchitectureEnforcer
from utils.copy_repo import copy_repo_to_workspace
from utils.tree_visualiser import print_tree
from utils.repo_scanner import build_module_map
from preflight_validator import preflight_validate
from task_memory import TaskMemory
from git_workflow import GitWorkflow

from work_item_planning import WorkItemPlanner
from validator import BuildTestValidator

from mcp_servers.ado_mcp_client import AdoMcpClient
from mcp_servers.github_mcp_client import GithubMcpClient


def _checkout_branch_for_resume(repo_path: Path, branch_name: str) -> bool:
    """
    Checks out an existing feature branch in the REAL repo before the
    temp workspace is copied from it, so a resumed run's scratch copy
    reflects everything already committed in previous runs instead of
    the original base branch.
    """
    def run_git(args):
        try:
            return subprocess.run(
                ["git", *args], cwd=repo_path, capture_output=True, text=True
            )
        except FileNotFoundError as ex:
            print(f"git is not available on PATH: {ex}")
            return None

    result = run_git(["checkout", branch_name])
    if result is not None and result.returncode == 0:
        return True

    run_git(["fetch", "origin", branch_name])
    result = run_git(["checkout", branch_name])
    if result is not None and result.returncode == 0:
        return True

    if result is not None:
        print(f"git checkout output:\n{result.stderr}")
    return False

class SupervisorAgent:
    """
    Async orchestrator with architecture checks:
        plan → decompose → execute → architecture → fixloop → validate → PR
    """

    def __init__(self, repo_path: Path, work_item_id: int, model_config: Dict[str, Any]):
        self.repo_path = repo_path
        self.work_item_id = work_item_id
        self.model_config = model_config

        self.temp_workspace: Optional[Path] = None
        self.repo_type: Optional[str] = None
        self.enforcer: Optional[CleanArchitectureEnforcer] = None
        self.module_map: Optional[Dict[str, Any]] = None

        self.run_state: Optional[RunState] = None
        self.resuming: bool = False

        root = Path(__file__).parent.parent
        self.ado = AdoMcpClient(str(root / "mcp-servers" / "ado" / "server.js"))
        self.github = GithubMcpClient(str(root / "mcp-servers" / "github" / "server.js"))

        # Agents
        self.planner = None
        self.decomposer = None
        self.executor = None
        self.fixloop = None
        self.validator_agent = None
        self.pr_agent = None
        self.arch_agent = None

    # ---------------------------------------------------------
    # Public entry point
    # ---------------------------------------------------------

    async def run(self):
        try:
            if not await self._load_or_resume_state():
                return
            if not await self._prepare_workspace():
                return

            await self._detect_repo_type()
            await self._init_enforcer_and_modules()
            await self._init_agents()

            plan = await self._ensure_plan()
            tasks = plan["tasks"]

            branch_name = await self._ensure_branch(plan)

            task_memory = TaskMemory()
            await self._execute_tasks(plan, tasks, branch_name, task_memory)

            build_ok, build_msg = await self._validate_repo()
            if not build_ok:
                # Must stop here -- the old main.py returned immediately
                # on a failed build/test validation rather than pushing
                # and opening a PR for code known not to build/pass
                # tests. That check was missing here: run() previously
                # fell straight through to _ensure_pr() regardless of
                # build_ok, which would have opened a PR advertising
                # broken code on every unfixable validation failure.
                print(f"Build and test validation failed: {build_msg}")
                return

            print(f"Build and test validation succeeded: {build_msg}")
            pr_url = await self._ensure_pr(plan, task_memory, build_msg, branch_name)

            await self._link_pr_to_work_item(pr_url)

            self.run_state.clear()

            print("\n=== COMPLETE ===")
            print({
                "work_item_id": self.work_item_id,
                "branch": branch_name,
                "pr_url": pr_url,
                "plan": plan,
            })

        finally:
            self.ado.close()
            self.github.close()

    # ---------------------------------------------------------
    # Init
    # ---------------------------------------------------------

    async def _load_or_resume_state(self) -> bool:
        """
        Returns False if the caller should abort the run cleanly (a
        message has already been printed explaining why). Deliberately
        does NOT raise for the "resume can't check out its branch"
        case -- that's an expected, user-actionable outcome (fix the
        branch manually, or delete the state file to start over), not
        a bug, and shouldn't surface as an unhandled traceback.
        """
        self.run_state = RunState.load(self.repo_path, self.work_item_id)
        self.resuming = self.run_state is not None

        if self.resuming:
            branch = self.run_state.branch_name
            print(f"\nResuming previous run for Work Item {self.work_item_id} on branch '{branch}'")

            if not _checkout_branch_for_resume(self.repo_path, branch):
                print(
                    f"Could not check out existing branch '{branch}' in {self.repo_path}. "
                    f"Aborting resume to avoid generating edits against the wrong base.\n"
                    f"Check out the branch manually and re-run, or delete {self.run_state.path} "
                    f"to start this Work Item over from scratch."
                )
                return False

        return True

    async def _prepare_workspace(self) -> bool:
        """
        Returns False if pre-flight failed and the run should stop
        cleanly. A repo that isn't backend/frontend, or that fails to
        build on its base branch, is an expected outcome the caller
        should be told about plainly -- not an unhandled exception.
        """
        self.temp_workspace = self.repo_path / ".orchestrator-tmp"
        if self.temp_workspace.exists():
            shutil.rmtree(self.temp_workspace, ignore_errors=True)
        self.temp_workspace.mkdir(parents=True, exist_ok=True)

        copy_repo_to_workspace(self.repo_path, self.temp_workspace)
        print_tree(self.temp_workspace, max_depth=3)

        ok, msg = preflight_validate(self.temp_workspace)
        if not ok:
            print(msg)
            return False

        print(msg)
        return True

    async def _detect_repo_type(self):
        self.repo_type = detect_repo_type(self.temp_workspace)

    async def _init_enforcer_and_modules(self):
        self.enforcer = CleanArchitectureEnforcer(self.temp_workspace, self.repo_type)
        module_root = self.temp_workspace / "src"
        self.module_map = build_module_map(module_root)

    async def _init_agents(self):
        self.planner = PlanningAgent(
            WorkItemPlanner(self.ado, self.model_config),
            self.model_config["planning_model"]
        )

        self.decomposer = DecompositionAgent(self.model_config["decomposition_model"])
        self.executor = ExecutionAgent(self.model_config["execution_model"])
        self.fixloop = FixLoopAgent(self.model_config["fixloop_model"])
        self.validator_agent = ValidationAgent(self.model_config["fixloop_model"])
        self.pr_agent = PRAgent()
        self.arch_agent = ArchitectureAgent()

    # ---------------------------------------------------------
    # Result handling
    # ---------------------------------------------------------

    @staticmethod
    def _unwrap(result, what: str):
        """
        Agent.run() no longer lets an exception from inside _execute()
        escape uncaught -- it's converted into
        AgentResult(success=False, error=...) so retries and the rest
        of the pipeline can't be crashed by one agent's internals (see
        agents/base/agent.py). That means every call site here needs
        to check `result.success` before touching `result.payload`,
        since payload is None on that failure path. This turns a
        failure into one clear, labelled RuntimeError instead of a
        confusing "NoneType is not subscriptable" a line later.
        """
        if not result.success:
            message = result.error.message if result.error else "unknown error"
            raise RuntimeError(f"{what} failed: {message}")
        return result.payload

    # ---------------------------------------------------------
    # Planning
    # ---------------------------------------------------------

    async def _ensure_plan(self):
        if self.resuming:
            return {
                "id": self.work_item_id,
                "title": self.run_state.plan_title,
                "tasks": self.run_state.tasks,
                "repo_type": self.repo_type,
            }

        ctx = ContextPacket(task_ctx={"work_item_id": self.work_item_id})
        result = await self.planner.run(ctx)

        plan = self._unwrap(result, "Planning")["plan"]
        plan["id"] = self.work_item_id
        plan["repo_type"] = self.repo_type

        # RunState isn't created/persisted here on purpose: a plan with
        # no branch yet isn't a safely resumable state (there'd be
        # nothing to check out on a crash between here and
        # _ensure_branch() actually creating one). init_plan() below
        # only runs once the branch genuinely exists, so plan and
        # branch are always persisted together.
        return plan

    # ---------------------------------------------------------
    # Branch
    # ---------------------------------------------------------

    async def _ensure_branch(self, plan):
        gitflow = GitWorkflow(self.repo_path, self.github, self.repo_type)

        if self.resuming:
            return self.run_state.branch_name

        branch_name = gitflow.make_branch_name(self.work_item_id, plan["title"])
        await gitflow.create_branch(branch_name)

        self.run_state = RunState(self.repo_path, self.work_item_id)
        self.run_state.init_plan(branch_name, plan["title"], plan["tasks"])

        return branch_name

    # ---------------------------------------------------------
    # Execution + Architecture Checks
    # ---------------------------------------------------------

    async def _execute_tasks(self, plan, tasks, branch_name, task_memory):
        gitflow = GitWorkflow(self.repo_path, self.github, self.repo_type)

        for task in tasks:
            if self.run_state.get_task(task["title"]) and self.run_state.get_task(task["title"])["done"]:
                continue

            # Decomposition
            if self.run_state.get_task(task["title"]) and self.run_state.get_task(task["title"])["subtasks"]:
                subtasks = self.run_state.get_task(task["title"])["subtasks"]
            else:
                ctx = ContextPacket(task_ctx={
                    "work_item_id": self.work_item_id,
                    "work_item_title": plan["title"],
                    "task": task,
                    "repo_type": self.repo_type,
                    "model_config": self.model_config,
                })
                result = await self.decomposer.run(ctx)
                subtasks = self._unwrap(result, "Decomposition")
                self.run_state.set_task_subtasks(task["title"], subtasks)

            # Execute subtasks
            for sub in subtasks:
                if self.run_state.is_subtask_done(task["title"], sub["title"]):
                    task_memory.add(task["title"], sub["title"], [], "(completed earlier)")
                    continue

                ctx = ContextPacket(task_ctx={
                    "repo_path": self.repo_path,
                    "workspace_path": self.temp_workspace,
                    "work_item_id": self.work_item_id,
                    "work_item_title": plan["title"],
                    "task": task,
                    "subtask": sub,
                    "repo_type": self.repo_type,
                    "enforcer": self.enforcer,
                    "model_config": self.model_config,
                })

                result = await self.executor.run(ctx)
                changed_files = self._unwrap(result, "Execution")

                # ARCHITECTURE CHECKS (defense-in-depth)
                #
                # execute_subtask() already validates every edit against
                # Clean Architecture rules internally (via
                # apply_file_edits_for_task()) and drops the whole
                # subtask's changes if the model proposed something
                # illegal, so in practice nothing illegal should reach
                # this loop. This is a second, independent check on top
                # of that -- and its failure mode matters: an illegal
                # path here must NOT raise and crash the whole run the
                # same way we fixed for execute_subtask() and FixLoop
                # earlier. Instead, drop just that file and keep going,
                # so one bad edit can't take down everything already
                # committed for earlier subtasks.
                safe_files = []
                for f in changed_files:
                    arch_ctx = ContextPacket(
                        task_ctx={"enforcer": self.enforcer},
                        micro_ctx={"path": f["path"]}
                    )
                    arch_result = await self.arch_agent.run(arch_ctx)

                    if arch_result.success:
                        safe_files.append(f)
                    else:
                        print(
                            f"--- Dropping illegal architecture path from subtask "
                            f"'{sub['title']}': {f['path']} ---"
                        )
                changed_files = safe_files

                # Commit
                if changed_files:
                    await gitflow.commit_task_changes(
                        branch_name=branch_name,
                        work_item_id=self.work_item_id,
                        task=sub,
                        changed_files=changed_files,
                    )
                else:
                    print(f"--- Subtask '{sub['title']}' produced no file changes; skipping commit ---")

                task_memory.add(task["title"], sub["title"], changed_files, "")
                self.run_state.mark_subtask_done(task["title"], sub["title"])

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    async def _validate_repo(self):
        if self.resuming and self.run_state.validated:
            return True, "Already validated"

        ctx = ContextPacket(task_ctx={
            "validator": BuildTestValidator(
                repo_path=self.repo_path,
                temp_workspace=self.temp_workspace,
                max_fix_attempts=3,
                repo_type=self.repo_type,
                enforcer=self.enforcer,
                model_config=self.model_config,
            )
        })

        result = await self.validator_agent.run(ctx)

        # Unlike _unwrap()'s call sites, a failed validation is a
        # normal, expected outcome here (not a crash condition) --
        # ValidationAgent._execute() always sets payload={"message":
        # ...} whether or not validation passed. payload is only ever
        # None if _execute() itself raised something unexpected, which
        # Agent.run() now converts into success=False with no payload;
        # fall back to the error message in that case instead of
        # crashing on `None["message"]`.
        if result.payload is not None:
            message = result.payload["message"]
        else:
            message = result.error.message if result.error else "Validation failed with no details"

        if result.success:
            self.run_state.mark_validated()

        return result.success, message

    # ---------------------------------------------------------
    # PR
    # ---------------------------------------------------------

    async def _ensure_pr(self, plan, task_memory, build_msg, branch_name):
        gitflow = GitWorkflow(self.repo_path, self.github, self.repo_type)

        if self.run_state.pr_url:
            return self.run_state.pr_url

        ctx = ContextPacket(task_ctx={
            "plan": plan,
            "task_memory": task_memory,
            "build_logs": build_msg,
        })

        pr_result = await self.pr_agent.run(ctx)
        pr_body = self._unwrap(pr_result, "PR description generation")["pr_body"]

        await gitflow.push_branch(branch_name)

        pr_url = await gitflow.open_pull_request(
            branch_name,
            plan["title"],
            pr_body,
        )

        self.run_state.mark_pr_opened(pr_url)
        return pr_url

    # ---------------------------------------------------------
    # Link PR
    # ---------------------------------------------------------

    async def _link_pr_to_work_item(self, pr_url):
        await self.ado.link_pr(self.work_item_id, pr_url)
