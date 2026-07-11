# 1.2.5 Phase 1 — Skill Routing

# Skill routing (making your skills actually work together)

Skill routing is the glue between:
*   your **context graph**    
*   your **skill registry**    
*   your **context profiles**
    
It’s the logic that decides:

> “Given the current state of the run, **which skill** should run next, and **what exact context packet** should it receive?”

You’re already doing this implicitly in `main.py`. Let’s make it explicit and clean.

Skill routing answers three questions for every step:

1.  **Who runs?** Which skill is appropriate for the current phase (planning, decomposition, execution, fixloop, validation, PR)?    
2.  **With what?** Which context layers (global, task, local, micro) are needed for that skill?    
3.  **In what shape?** How do we slice/compress that context into the skill’s context profile?    

# Your current routing (already in main.py)

You already have a routing pipeline:

*   **Planner** Called once per work item:
    *   Input: work item from ADO MCP + repo type + module map        
    *   Output: `plan`
  
*   **Decomposer** Called per task:
    *   Input: `plan["title"]`, `task`, `repo_type`, `model_config`        
    *   Output: `subtasks`        
    *   Persisted in `RunState`
        
*   **Executor** Called per subtask:
    *   Input: `repo_path`, `temp_workspace`, `work_item_id`, `plan["title"]`, `task`, `sub`, `repo_type`, `enforcer`, `model_config`        
    *   Output: `changed_files`
        
*   **Validator** Called once after tasks:
    *   Input: `repo_path`, `temp_workspace`, `repo_type`, `enforcer`, `model_config`        
    *   Output: `ok, message`
        
*   **PR Enhancer** Called once after validation:
    *   Input: `plan`, `task_memory`, `message`        
    *   Output: `pr_body`
        
*   **RunState** Called throughout:
    *   Input/Output: plan, tasks, subtasks, validation, PR URL
        
That’s already skill routing—just not named as such.

# Making routing explicit

You can think of routing as a simple dispatcher:

```
    def route_skill(skill_name, global_ctx, task_ctx, local_ctx, micro_ctx):
        profile = SKILL_REGISTRY[skill_name]["context_profile"]
        ctx = build_context_packet(profile, global_ctx, task_ctx, local_ctx, micro_ctx)
        return SKILL_REGISTRY[skill_name]["handler"](ctx)
```  

Where:

*   `context_profile` says what the skill is allowed to see    
*   `build_context_packet` slices/compresses accordingly    
*   `handler` is the actual implementation (planner, decomposer, executor, etc.)
    
You don’t need to implement this right now—but thinking this way makes your system extensible.

# Routing rules in your orchestrator

In your current design:

*   **Global context** is built once (repo type, module map, enforcer).    
*   **Task context** comes from `plan` and `RunState`.    
*   **Local context** comes from `temp_workspace`.    
*   **Micro context** comes from the current `task` + `subtask` + error slice.
    
Routing is:

*   Planner → global + work item    
*   Decomposer → global + task    
*   Executor → local + micro    
*   FixLoop → local + micro (error)    
*   Validator → global + local (build/test)    
*   PR Enhancer → task + memory + validation
    
You’re already doing correct routing; the next step is just to **treat it as a first‑class concept**.

# Why this matters for you

Once routing is explicit, you can:

*   swap models per skill without touching `main.py`    
*   add new skills (e.g. “Doc Generator”, “Refactorer”) by registering them    
*   change context profiles centrally    
*   log per-skill inputs/outputs for debugging    
*   add a supervisor agent later that inspects routing decisions
    
You’re already very close to that—your orchestrator is effectively a routed skill graph.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Skill Context Profiles](./12-phase1-skill-context-profiles.md)
