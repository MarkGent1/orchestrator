# 1. Module 1: Work Item + Plan + Tasks

# 1.1 Overview

This module gives your orchestrator the ability to:

1.  Read the ADO Work Item    
2.  Validate acceptance criteria    
3.  Generate a task plan    
4.  Create child tasks in ADO    
5.  Update the Work Item state    
6.  Add comments summarising the plan
7.  Returns plan to the orchestrator core
    
This is the “outer loop brain” and the **entry point** for the entire SDLC loop.

## 1.2. High‑level flow

```
User says: “Implement feature X”

↓ Orchestrator does:

1. Read Work Item from ADO MCP
2. Extract:
   - Title
   - Description
   - Acceptance Criteria
   - Tags
   - Area Path
   - Iteration Path
3. Validate Work Item quality
4. Generate a structured task plan
5. Create child tasks via ADO MCP
6. Add a comment summarising the plan
7. Update Work Item state → Active
8. Return plan to user
```

## 1.3. Getting started guide

### 1.3.1 Where this code should live

Keep it **separate from your MCP servers**, but in the **same workspace**. Example structure:

```
<dev-root>/
  mcp-servers/
  orchestrator/
    work_item_planning.py
    ado_client_stub.py
    main.py
```

The orchestrator will _call_ your MCP servers; it doesn’t need to live inside them.

### 1.3.2 Create the `orchestrator` folder + venv

```
mkdir orchestrator
cd orchestrator

python -m venv .venv
# Windows PowerShell:
. .venv/Scripts/Activate.ps1

# or Git Bash:
source .venv/Scripts/activate
```

Note. In VS Code with the Python extension installed it works nicely using `F1 + Command > Python: Create Environment` and select `.venv`.

Once completed, run:

`. .venv/Scripts/Activate.ps1`

In VS Code:

*   Bottom-right: select Python interpreter → pick `.venv`.

No extra packages needed yet.

### 1.3.3. Add a fake ADO client so we can run this without MCP

```
class FakeAdoClient:
    async def get_work_item(self, work_item_id: int):
        return {
            "id": work_item_id,
            "fields": {
                "System.Title": "As a user, I can export reports",
                "System.Description": "As a user I want to export reports so that I can share them.",
                "Microsoft.VSTS.Common.AcceptanceCriteria": "- Export as CSV\n- Export as PDF",
            },
        }

    async def create_child_task(self, parent_id: int, title: str, description: str):
        # In reality this would call ADO MCP; for now we just fake it
        return {
            "id": 1000,  # pretend ID
            "fields": {
                "System.Title": title,
                "System.Description": description,
            },
        }

    async def add_comment(self, work_item_id: int, text: str):
        print(f"\n--- COMMENT ON WI {work_item_id} ---\n{text}\n--- END COMMENT ---\n")

    async def update_work_item_state(self, work_item_id: int, state: str):
        print(f"[stub] Updating Work Item {work_item_id} state → {state}")
```

### 1.3.4. Add `work_item_planning.py`

```
class WorkItemPlanner:
    def __init__(self, ado_mcp_client):
        self.ado = ado_mcp_client

    async def plan_work_item(self, work_item_id: int):
        wi = await self.ado.get_work_item(work_item_id)

        title = wi["fields"].get("System.Title", "")
        description = wi["fields"].get("System.Description", "")
        acceptance = wi["fields"].get("Microsoft.VSTS.Common.AcceptanceCriteria", "")

        quality_issues = self.validate_work_item(title, description, acceptance)
        plan = self.generate_task_plan(title, description, acceptance)

        created_tasks = []
        for task in plan["tasks"]:
            created = await self.ado.create_child_task(
                parent_id=work_item_id,
                title=task["title"],
                description=task["description"],
            )
            created_tasks.append(created)

        await self.ado.add_comment(
            work_item_id,
            self.render_plan_comment(plan, created_tasks, quality_issues),
        )

        await self.ado.update_work_item_state(work_item_id, "Active")

        return {
            "plan": plan,
            "created_tasks": created_tasks,
            "quality_issues": quality_issues,
        }

    def validate_work_item(self, title, description, acceptance):
        issues = []

        if len(title.strip()) < 5:
            issues.append("Title is too short.")

        if not description or len(description.strip()) < 20:
            issues.append("Description is missing or too short.")

        if not acceptance:
            issues.append("Acceptance Criteria missing.")

        if "As a" not in description and "I want" not in description:
            issues.append("User story format missing.")

        return issues

    def generate_task_plan(self, title, description, acceptance):
        return {
            "title": title,
            "tasks": [
                {
                    "title": f"Analyse Work Item: {title}",
                    "description": "Review the Work Item, acceptance criteria, and dependencies.",
                },
                {
                    "title": "Design solution",
                    "description": "Define data structures, API changes, and architecture impacts.",
                },
                {
                    "title": "Implement backend changes",
                    "description": "Write code, update models, add business logic.",
                },
                {
                    "title": "Implement frontend changes",
                    "description": "Update UI components, forms, and validation.",
                },
                {
                    "title": "Write automated tests",
                    "description": "Unit tests, integration tests, and acceptance tests.",
                },
                {
                    "title": "Update documentation",
                    "description": "Update README, ADRs, and API docs.",
                },
            ],
        }

    def render_plan_comment(self, plan, created_tasks, issues):
        comment = "### 🧠 Work Item Plan Generated\n\n"

        if issues:
            comment += "#### ⚠️ Quality Issues Detected\n"
            for issue in issues:
                comment += f"- {issue}\n"
            comment += "\n"

        comment += "#### 📋 Task Plan\n"
        for t in plan["tasks"]:
            comment += f"- **{t['title']}** — {t['description']}\n"

        comment += "\n#### 🆕 Created Tasks\n"
        for t in created_tasks:
            comment += f"- {t['id']}: {t['fields']['System.Title']}\n"

        return comment
```

### 1.3.5. Add a tiny `main.py` to run + debug

```
import asyncio
from ado_client_stub import FakeAdoClient
from work_item_planning import WorkItemPlanner


async def main():
    ado = FakeAdoClient()
    planner = WorkItemPlanner(ado)

    result = await planner.plan_work_item(work_item_id=123)

    print("\n=== PLAN RESULT ===")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

Now you can run:

```
python main.py
```

You should see:
*   printed “stub” updates    
*   the generated comment    
*   the plan result dict

### 1.3.6. Debugging in VS Code

1.  In VS Code, open the `orchestrator` folder (or the root with it inside).    
2.  Go to **Run and Debug** (left sidebar).    
3.  Click **“create a launch.json”** → choose **Python: Current File**.    
4.  Ensure it points at `main.py` (or just open `main.py` and hit F5).
    
Set a breakpoint inside `plan_work_item` or `validate_work_item`, hit F5, and you’ll be stepping through the orchestrator logic.

## 1.4. Replace the stub with a real ADO MCP client wrapper

This means:

*   your orchestrator will call your ADO MCP server    
*   the MCP server will call Azure DevOps    
*   the orchestrator will receive real Work Items    
*   the orchestrator will create real Tasks    
*   the orchestrator will add real comments    
*   the orchestrator will update real Work Item state
    
This is where it becomes _real_.

### 1.4.1 Add a new AdoMcpClient

```
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
```

### 1.4.2 Update the main entry point to use the new AdoMcpClient

```
import asyncio
import sys
from ado_mcp_client import AdoMcpClient
from work_item_planning import WorkItemPlanner
from pathlib import Path

async def main():
    SERVER_PATH = str(Path(__file__).parent.parent / "mcp-servers" / "ado" / "server.js")

    if len(sys.argv) < 2:
        raise ValueError("Usage: python main.py <work_item_id>")

    work_item_id = int(sys.argv[1])

    ado = AdoMcpClient(SERVER_PATH)
    planner = WorkItemPlanner(ado)

    result = await planner.plan_work_item(work_item_id=work_item_id)

    print("\n=== PLAN RESULT ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

Add .env file for your variables:

```
ENV=local
ADO_ORG=XXXX
ADO_PROJECT=XXXX
ADO_PAT=XXXX
GITHUB_TOKEN=XXXX
```

### 1.4.3 Update launch.js to ask for work item id

```
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run Orchestrator (Work Item)",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "args": [
                "${input:workItemId}"
            ]
        }
    ],
    "inputs": [
        {
            "id": "workItemId",
            "type": "promptString",
            "description": "Enter Work Item ID",
            "default": "151"
        }
    ]
}
```

[<< Overview](../../README.md)
 | 
[<< Advancing the Orchestrator](./1-advancing-the-orchestrator.md)
 | 
[Module 2: Branch + PR Automation >>](./3-module-2.md)
