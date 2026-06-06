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