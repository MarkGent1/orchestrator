import subprocess
import threading
import json
import uuid
import os
import asyncio
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

    DEFAULT_TIMEOUT_SECONDS = 120

    def __init__(self, server_path: str, timeout: float = DEFAULT_TIMEOUT_SECONDS):
        server_path = str(Path(server_path))
        self.timeout = timeout

        self.proc = subprocess.Popen(
            ["node", server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            env={**os.environ},
        )

        print("Started MCP server:", self.proc.pid)

        # Drain stderr continuously in the background. If nobody reads
        # it, a chatty child process can fill the OS pipe buffer and
        # block on write -- which would then block our stdout reads
        # forever with no visible error. Draining also surfaces the
        # server's own error/debug logs instead of silently discarding
        # them.
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()

    def _drain_stderr(self):
        try:
            for line in iter(self.proc.stderr.readline, b""):
                if line:
                    print(f"[GitHub MCP stderr] {line.decode('utf-8', errors='replace').rstrip()}")
        except Exception:
            pass

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    async def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Low-level JSON-RPC call helper.
        """
        if not self.proc.stdin or not self.proc.stdout:
            raise RuntimeError("MCP process not initialized with pipes")

        if self.proc.poll() is not None:
            raise RuntimeError(
                f"GitHub MCP server process has already exited (code {self.proc.returncode})"
            )

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

        loop = asyncio.get_event_loop()

        while True:
            if self.proc.poll() is not None:
                raise RuntimeError(
                    f"GitHub MCP server exited unexpectedly (code {self.proc.returncode}) "
                    f"while waiting for a response to '{method}'"
                )

            try:
                # readline() blocks; run it off the event loop so a
                # slow/hung server doesn't freeze the whole orchestrator,
                # and so we can bound the wait with a timeout instead of
                # hanging forever.
                line = await asyncio.wait_for(
                    loop.run_in_executor(None, self.proc.stdout.readline),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                raise RuntimeError(
                    f"Timed out after {self.timeout}s waiting for GitHub MCP response to '{method}'"
                )

            if not line:
                code = self.proc.poll()
                raise RuntimeError(
                    f"GitHub MCP server closed its stdout unexpectedly (exit code {code}) "
                    f"while waiting for a response to '{method}'"
                )

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
