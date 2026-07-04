import asyncio

import pytest

from work_item_planning import WorkItemPlanner


class FakeAdoClient:
    def __init__(self, work_item, existing_children=None):
        self.work_item = work_item
        self.existing_children = existing_children or {}
        self.created_tasks = []
        self.comments = []
        self.state_updates = []

    async def get_work_item(self, id):
        if id == self.work_item["id"]:
            return self.work_item
        if id in self.existing_children:
            return self.existing_children[id]
        raise RuntimeError(f"no such work item {id}")

    async def create_child_task(self, parent_id, title, description):
        task = {"id": 1000 + len(self.created_tasks), "fields": {"System.Title": title, "System.Description": description}}
        self.created_tasks.append(task)
        return task

    async def add_comment(self, id, text):
        self.comments.append((id, text))
        return {}

    async def update_work_item_state(self, id, state):
        self.state_updates.append((id, state))
        return {}


def _work_item(id=404, relations=None):
    return {
        "id": id,
        "fields": {
            "System.Title": "Add UsersController",
            "System.Description": "As a user I want to manage users so that I can administer the system.",
            "Microsoft.VSTS.Common.AcceptanceCriteria": "Given/When/Then...",
        },
        "relations": relations,
    }


def test_plan_work_item_generates_new_plan_when_no_existing_children(monkeypatch, model_config):
    ado = FakeAdoClient(_work_item(relations=[]))
    planner = WorkItemPlanner(ado, model_config)

    async def fake_call_model_json(prompt, model, provider):
        return [{"title": "Sub A", "description": "d1"}, {"title": "Sub B", "description": "d2"}]

    monkeypatch.setattr("work_item_planning.call_model_json", fake_call_model_json)

    result = asyncio.run(planner.plan_work_item(404))

    assert [t["title"] for t in result["plan"]["tasks"]] == ["Sub A", "Sub B"]
    assert len(result["created_tasks"]) == 2
    assert len(ado.created_tasks) == 2
    assert len(ado.comments) == 1
    assert ado.state_updates == [(404, "Active")]


def test_plan_work_item_reuses_existing_child_tasks_without_calling_model(monkeypatch, model_config):
    child = {"id": 500, "fields": {"System.Title": "Existing Sub", "System.Description": "already planned"}}
    relations = [{"rel": "System.LinkTypes.Hierarchy-Forward", "url": "https://dev.azure.com/org/proj/_apis/wit/workItems/500"}]
    ado = FakeAdoClient(_work_item(relations=relations), existing_children={500: child})
    planner = WorkItemPlanner(ado, model_config)

    model_called = []

    async def fake_call_model_json(prompt, model, provider):
        model_called.append(True)
        return []

    monkeypatch.setattr("work_item_planning.call_model_json", fake_call_model_json)

    result = asyncio.run(planner.plan_work_item(404))

    assert model_called == []
    assert result["plan"]["tasks"] == [{"title": "Existing Sub", "description": "already planned"}]
    assert result["created_tasks"] == []
    assert ado.created_tasks == []  # no duplicate child tasks created
    assert ado.comments == []  # no duplicate "plan generated" comment
    assert ado.state_updates == []  # state not re-transitioned


def test_get_existing_child_tasks_ignores_non_hierarchy_forward_relations(model_config):
    relations = [{"rel": "System.LinkTypes.Related", "url": "https://dev.azure.com/org/proj/_apis/wit/workItems/999"}]
    ado = FakeAdoClient(_work_item(relations=relations))
    planner = WorkItemPlanner(ado, model_config)

    result = asyncio.run(planner._get_existing_child_tasks(ado.work_item))
    assert result == []


def test_get_existing_child_tasks_fails_open_when_relations_key_missing(model_config):
    wi = _work_item(relations=None)
    del wi["relations"]
    ado = FakeAdoClient(wi)
    planner = WorkItemPlanner(ado, model_config)

    result = asyncio.run(planner._get_existing_child_tasks(wi))
    assert result == []


def test_get_existing_child_tasks_skips_broken_child_link(model_config):
    relations = [{"rel": "System.LinkTypes.Hierarchy-Forward", "url": ".../wit/workItems/9999"}]
    ado = FakeAdoClient(_work_item(relations=relations), existing_children={})  # 9999 not resolvable
    planner = WorkItemPlanner(ado, model_config)

    result = asyncio.run(planner._get_existing_child_tasks(ado.work_item))
    assert result == []


def test_plan_work_item_raises_when_model_returns_non_list(monkeypatch, model_config):
    ado = FakeAdoClient(_work_item(relations=[]))
    planner = WorkItemPlanner(ado, model_config)

    async def fake_call_model_json(prompt, model, provider):
        return {"not": "a list"}

    monkeypatch.setattr("work_item_planning.call_model_json", fake_call_model_json)

    with pytest.raises(ValueError):
        asyncio.run(planner.plan_work_item(404))


@pytest.mark.parametrize("title,description,acceptance,expected_issue_substring", [
    ("Hi", "As a user I want X so that Y, this is long enough.", "criteria", "Title is too short"),
    ("A valid title", "short", "criteria", "Description is missing or too short"),
    ("A valid title", "As a user I want X so that Y, this is long enough.", "", "Acceptance Criteria missing"),
    ("A valid title", "This description has no user story format at all here.", "criteria", "User story format missing"),
])
def test_validate_work_item_flags_quality_issues(model_config, title, description, acceptance, expected_issue_substring):
    ado = FakeAdoClient(_work_item())
    planner = WorkItemPlanner(ado, model_config)
    issues = planner.validate_work_item(title, description, acceptance)
    assert any(expected_issue_substring in issue for issue in issues)


def test_validate_work_item_no_issues_for_well_formed_input(model_config):
    ado = FakeAdoClient(_work_item())
    planner = WorkItemPlanner(ado, model_config)
    issues = planner.validate_work_item(
        "Add UsersController",
        "As a user I want to manage users so that I can administer the system.",
        "Given/When/Then...",
    )
    assert issues == []
