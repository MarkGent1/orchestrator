from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

from agents.base.agent import ContextPacket, AgentError
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
            await self._load_or_resume_state()
            await self._prepare_workspace()
            await self._detect_repo_type()
            await self._init_enforcer_and_modules()
            await self._init_agents()

            plan = await self._ensure_plan()
            tasks = plan["tasks"]

            branch_name = await self._ensure_branch(plan)

            task_memory = TaskMemory()
            await self._execute_tasks(plan, tasks, branch_name, task_memory)

            build_ok, build_msg = await self._validate_repo()
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

    async def _load_or_resume_state(self):
        self.run_state = RunState.load(self.repo_path, self.work_item_id)
        self.resuming = self.run_state is not None

    async def _prepare_workspace(self):
        self.temp_workspace = self.repo_path / ".orchestrator-tmp"
        if self.temp_workspace.exists():
            shutil.rmtree(self.temp_workspace, ignore_errors=True)
        self.temp_workspace.mkdir(parents=True, exist_ok=True)

        copy_repo_to_workspace(self.repo_path, self.temp_workspace)
        print_tree(self.temp_workspace, max_depth=3)

        ok, msg = preflight_validate(self.temp_workspace)
        if not ok:
            raise RuntimeError(msg)

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

        plan = result.payload["plan"]
        plan["id"] = self.work_item_id
        plan["repo_type"] = self.repo_type

        self.run_state = RunState(self.repo_path, self.work_item_id)
        self.run_state.init_plan(None, plan["title"], plan["tasks"])

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

        self.run_state.branch_name = branch_name
        self.run_state.save()

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
                subtasks = result.payload
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
                changed_files = result.payload

                # ARCHITECTURE CHECKS
                for f in changed_files:
                    arch_ctx = ContextPacket(
                        task_ctx={"enforcer": self.enforcer},
                        micro_ctx={"path": f["path"]}
                    )
                    arch_result = await self.arch_agent.run(arch_ctx)

                    if not arch_result.success:
                        raise AgentError(
                            type="architecture_error",
                            message=f"Illegal architecture path: {f['path']}",
                            details=arch_result.error.details,
                        )

                # Commit
                if changed_files:
                    await gitflow.commit_task_changes(
                        branch_name=branch_name,
                        work_item_id=self.work_item_id,
                        task=sub,
                        changed_files=changed_files,
                    )

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

        if result.success:
            self.run_state.mark_validated()

        return result.success, result.payload["message"]

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
        pr_body = pr_result.payload["pr_body"]

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
