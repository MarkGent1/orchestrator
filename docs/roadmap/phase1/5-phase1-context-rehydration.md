# 1.1.4 Phase 1 — Context rehydration

This is the skill of letting an agent **wake up mid‑run** and reconstruct everything it needs to keep going without starting from scratch.

Let’s anchor this directly in your orchestrator.

# The three sources of rehydration

You already have three distinct “memory surfaces”:
*   Global context (rebuild from repo)
    *   `repo_path`        
    *   `temp_workspace`        
    *   `detect_repo_type(temp_workspace)`        
    *   `build_module_map(module_root)`        
    *   `CleanArchitectureEnforcer(temp_workspace, repo_type)`
        
*   Task context (rehydrate from RunState)
    *   `RunState.load(repo_path, work_item_id)`        
    *   `branch_name`        
    *   `plan_title`        
    *   `tasks` (titles, descriptions, done flags, subtasks)        
    *   `validated`        
    *   `pr_url`
        
*   Local context (rehydrate from workspace)
    *   copied repo in `.orchestrator-tmp`        
    *   current file contents        
    *   tests        
    *   architecture rules per module
        
Those three together are your **rehydration backbone**.

# How the orchestrator already rehydrates

You’re doing this in `main()`:

*   **Step 1: Load RunState**

```
run_state = RunState.load(repo_path, work_item_id)
resuming = run_state is not None        
```
 
*   **Step 2: Check out the feature branch in the real repo**

```    
_checkout_branch_for_resume(repo_path, run_state.branch_name)
```

*   **Step 3: Recreate temp workspace from that branch**

```    
copy_repo_to_workspace(repo_path, temp_workspace)        
```
 
*   **Step 4: Rebuild global/local context**

```    
repo_type = detect_repo_type(temp_workspace)
enforcer = CleanArchitectureEnforcer(temp_workspace, repo_type)
module_map = build_module_map(temp_workspace / "src")        
```
 
*   **Step 5: Rehydrate the plan** If resuming:

```
plan = {
    "id": work_item_id,
    "repo_type": repo_type,
    "title": run_state.plan_title,
    "tasks": [
        {"title": t["title"], "description": t["description"]}
        for t in run_state.tasks
    ],
}
branch_name = run_state.branch_name        
```
   
*   **Step 6: Resume task/subtask loop**

```
for task in tasks:
    task_state = run_state.get_task(task["title"])
    if task_state and task_state["done"]:
        # skip whole task
    else:
        # use persisted subtasks if present
        if task_state and task_state.get("subtasks"):
            subtasks = [...]
        else:
            subtasks = await decompose_task(...)
            run_state.set_task_subtasks(...)        
```

This is **full context rehydration**:
*   global → from repo    
*   task → from RunState    
*   local → from temp workspace    
*   micro → from current subtask    

# The key design choices you got right

*   **You rehydrate from the feature branch, not the base branch** So the temp workspace reflects all previous commits.    
*   **You persist decomposition once and reuse it** So resumed runs don’t get a different subtask breakdown.    
*   **You mark subtasks done and skip them on resume** So you never redo completed work.    
*   **You mark validation and PR state** So you don’t rerun build/tests or reopen PRs.
    
This is exactly how a robust agentic system should behave.

# Where you can extend rehydration next

If you want to deepen this:
*   Rehydrate micro context
    *   Persist last failing subtask + error slice        
    *   On resume, jump straight into the failing fixloop
        
*   Rehydrate task memory
    *   Persist `TaskMemory` snapshots        
    *   Use them to enrich PR summaries or debugging
        
*   Rehydrate model context
    *   Persist which model handled which skill last time        
    *   Use that to adapt future runs (e.g. “Haiku struggled here, use Sonnet next time”)

# The mental model to keep

Rehydration is always:
*   **Global** from repo    
*   **Task** from RunState    
*   **Local** from workspace    
*   **Micro** from current subtask/error
    
You’ve already implemented that pattern. Now you can treat it as a **first‑class design principle** in every new agent you build.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Context Compression](./4-phase1-context-compression.md)
 | 
[Phase 1 — Context boundaries >>](./6-phase1-context-boundaries.md)
