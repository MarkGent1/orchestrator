from pathlib import Path

import supervisor.supervisor_agent as supervisor_module
from supervisor.supervisor_agent import SupervisorAgent


class _CapturingAdo:
    def __init__(self, server_path):
        _CapturingAdo.captured_path = server_path

    def close(self):
        pass


class _CapturingGithub:
    def __init__(self, server_path):
        _CapturingGithub.captured_path = server_path

    def close(self):
        pass


def test_mcp_server_paths_resolve_outside_the_orchestrator_project_dir(monkeypatch):
    """
    Regression test: the real mcp-servers/ directory (the Node.js
    server.js processes for ADO and GitHub) lives as a SIBLING of the
    orchestrator project, not nested inside it. main.py used to
    compute this correctly with two `.parent` calls because it lived
    directly at <orchestrator>/main.py. When that logic moved into
    SupervisorAgent -- one folder deeper, at
    <orchestrator>/supervisor/supervisor_agent.py -- it kept the same
    two `.parent` calls, landing one level too shallow
    (<orchestrator>/mcp-servers/... instead of the real sibling path)
    and crashing both MCP clients on startup with MODULE_NOT_FOUND.

    This asserts the invariant directly (mcp-servers/ must NOT be
    inside the orchestrator project directory) rather than just
    re-deriving the same .parent chain the production code uses, so
    it still catches the bug if supervisor_agent.py ever moves again
    without the path math being updated to match.
    """
    monkeypatch.setattr(supervisor_module, "AdoMcpClient", _CapturingAdo)
    monkeypatch.setattr(supervisor_module, "GithubMcpClient", _CapturingGithub)

    SupervisorAgent(repo_path=Path("/whatever"), work_item_id=1, model_config={})

    orchestrator_project_dir = Path(supervisor_module.__file__).resolve().parent.parent
    ado_path = Path(_CapturingAdo.captured_path).resolve()
    github_path = Path(_CapturingGithub.captured_path).resolve()

    for path in (ado_path, github_path):
        assert orchestrator_project_dir not in path.parents, (
            f"{path} resolved inside the orchestrator project dir "
            f"({orchestrator_project_dir}) -- mcp-servers/ should be a "
            f"sibling directory, not nested inside the project."
        )
        assert path.name == "server.js"
        assert path.parent.parent.name == "mcp-servers"
