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
