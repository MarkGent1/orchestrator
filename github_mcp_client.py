import subprocess
import json
import uuid
import os
from pathlib import Path
from typing import Any, Dict, List

class GithubMcpClient:
    def __init__(self, server_path: str):
        server_path = str(Path(server_path))
        
        # Launch Node MCP server in binary mode (Windows-safe)
        self.proc = subprocess.Popen(
            ["node", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env={
                **os.environ,  # includes .env values
            }
        )

        print("Started MCP server:", self.proc.pid)

    async def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": method,
                "arguments": params
            }
        }

        # Write JSON-RPC request as bytes
        message = (json.dumps(payload) + "\n").encode("utf-8")
        self.proc.stdin.write(message)
        self.proc.stdin.flush()

        # Read response lines as bytes
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("MCP server closed")

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

    async def create_branch(self, repo_path: Path, branch_name: str) -> Dict[str, Any]:
        return await self._call("createBranch", {
            "repoPath": str(repo_path),
            "branchName": branch_name,
        })

    async def commit_files(
        self,
        repo_path: Path,
        branch_name: str,
        message: str,
        files: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return await self._call("commitFiles", {
            "repoPath": str(repo_path),
            "branchName": branch_name,
            "message": message,
            "files": files,
        })

    async def push_branch(self, repo_path: Path, branch_name: str) -> Dict[str, Any]:
        return await self._call("pushBranch", {
            "repoPath": str(repo_path),
            "branchName": branch_name,
        })

    async def open_pull_request(
        self,
        repo_path: Path,
        branch_name: str,
        title: str,
        body: str,
    ) -> Dict[str, Any]:
        result = await self._call("openPullRequest", {
            "repoPath": str(repo_path),
            "branchName": branch_name,
            "title": title,
            "body": body,
        })
        return result["structuredContent"]["prUrl"]
