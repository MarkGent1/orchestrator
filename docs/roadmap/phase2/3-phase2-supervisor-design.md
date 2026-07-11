# 2.2 Phase 2 — Supervisor design

The supervisor is the “brain” of the orchestrator.

It decides:

*   **which agent runs next**    
*   **what context packet to give it**    
*   **how to react to failures**    
*   **how to update RunState**    
*   **when to resume**    
*   **when to stop**    

### Supervisor responsibilities:

#### ✔ 1. Read RunState

Determine:
*   current task    
*   current subtask    
*   validation status    
*   PR status    
*   branch name    
*   resume point    

#### ✔ 2. Build Context Packets

Using:
*   global context    
*   task context    
*   local context    
*   micro context    

#### ✔ 3. Invoke the correct agent

Based on:
*   run phase    
*   task progress    
*   error state    
*   validation state    

#### ✔ 4. Handle failures

Call:
*   FixLoop agent    
*   Retry logic    
*   Fallback models    
*   Abort conditions    

#### ✔ 5. Update RunState

Persist:
*   subtasks done    
*   validation done    
*   PR opened    
*   branch name    
*   plan title    

#### ✔ 6. Produce logs

Per-agent logs:
*   inputs    
*   outputs    
*   errors    
*   retries    
*   decisions
    
This is the **core of Phase 2**.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 2 — Agent role definitions](./2-phase2-agent-roles.md)
 | 
[Phase 2 — Agent interfaces  >>](./4-phase2-agent-interfaces.md)
