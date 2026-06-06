import subprocess
import json
import uuid
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()  # loads .env into os.environ

class AdoMcpClient:
    def __init__(self, server_path):
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

    async def _call(self, method, params):
        request_id = str(uuid.uuid4())

        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": method,       # e.g. "getWorkItem"
                "arguments": params   # e.g. {"id": 151}
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

    async def get_work_item(self, id: int):
        result = await self._call("getWorkItem", {"id": id})
        return result["structuredContent"]["workItem"]

    async def update_work_item(self, id: int, fields: dict):
        result = await self._call("updateWorkItem", {"id": id, "fields": fields})
        return result["structuredContent"]["workItem"]

    async def add_comment(self, id: int, text: str):
        result = await self._call("addWorkItemComment", {"id": id, "text": text})
        return result["structuredContent"]["comment"]

    async def link_pr(self, id: int, pr_url: str):
        result = await self._call("linkPullRequest", {"id": id, "prUrl": pr_url})
        return result["structuredContent"]["workItem"]
    
    async def create_child_task(self, parent_id: int, title: str, description: str):
        result = await self._call("createChildTask", {
            "parentId": parent_id,
            "title": title,
            "description": description
        })
        return result["structuredContent"]["workItem"]
    
    async def update_work_item_state(self, id: int, state: str):
        result = await self._call("updateWorkItem", {
            "id": id,
            "fields": {
                "System.State": state
            }
        })
        return result["structuredContent"]["workItem"]
