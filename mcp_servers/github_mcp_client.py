import subprocess
import json
import uuid
import os
from pathlib import Path
from typing import Any, Dict, List


class GithubMcpClient:
    """
    Thin JSON-RPC client for the GitHub MCP server.

    Responsibilities:
    - Start the Node MCP server as a child process
    - Send JSON-RPC requests over stdin
    - Read JSON-RPC responses from stdout
    - Expose a small, typed public API for the orchestrator
    """

    def __init__(self, server_path: str):
        server_path = str(Path(server_path))

        self.proc = subprocess.Popen(
            ["node", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env={**os.environ},
        )

        print("Started MCP server:", self.proc.pid)

    async def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Low-level JSON-RPC call helper.
        """
        if not self.proc.stdin or not self.proc.stdout:
            raise RuntimeError("MCP process not initialized with pipes")

        request_id = str(uuid.uuid4())

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": method,
                "arguments": params,
            },
        }

        message = (json.dumps(payload) + "\n").encode("utf-8")
        self.proc.stdin.write(message)
        self.proc.stdin.flush()

        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("GitHub MCP server closed")

            try:
                msg = json.loads(line.decode("utf-8"))
            except json.JSONDecodeError:
                continue

            if msg.get("id") == request_id:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg["result"]

    # ---------------------------------------------------------
    # Public API — these MUST exist for the orchestrator
    # ---------------------------------------------------------

    async def create_branch(self, repo_path: str, branch_name: str) -> Dict[str, Any]:
        return await self._call(
            "createBranch",
            {
                "repoPath": repo_path,
                "branchName": branch_name,
            },
        )

    async def commit_files(
        self,
        repo_path: str, 
        branch_name: str,
        message: str,
        files: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return await self._call(
            "commitFiles",
            {
                "repoPath": repo_path,
                "branchName": branch_name,
                "message": message,
                "files": files,
            },
        )

    async def push_branch(self, repo_path: str, branch_name: str) -> Dict[str, Any]:
        return await self._call(
            "pushBranch",
            {
                "repoPath": repo_path,
                "branchName": branch_name,
            },
        )

    async def open_pull_request(
        self,
        repo_path: str, 
        branch_name: str,
        title: str,
        body: str,
    ) -> str:
        result = await self._call(
            "openPullRequest",
            {
                "repoPath": repo_path,
                "branchName": branch_name,
                "title": title,
                "body": body,
            },
        )

        # Be tolerant of different server response shapes
        if isinstance(result, dict):
            if "structuredContent" in result:
                return result["structuredContent"].get("prUrl")
            if "prUrl" in result:
                return result["prUrl"]

        return str(result)
