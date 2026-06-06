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
