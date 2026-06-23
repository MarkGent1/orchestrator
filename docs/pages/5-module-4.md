# 4. Module 4: Multi‑Task, Multi‑Phase, Multi‑Commit SDLC Loop

# 4.1 Overview

Module 4 introduces a **multi‑phase SDLC execution engine**:

    Work Item → Plan → Task Decomposition → Sub‑Task Loop → Multi‑Pass Refinement → Commit → Validate → PR Enhancement
    
It ensures:
*   Tasks are broken down into smaller, safer units    
*   Each sub‑task is executed cleanly    
*   Each pass improves the code    
*   Errors are fixed automatically    
*   PRs contain rich context
    
This is the orchestrator’s **inner loop brain**.

# 4.2 Task Decomposition

`task_decomposer.py` uses Claude to break a task into sub‑tasks:

    [
      { "title": "Add DTO", "description": "..." },
      { "title": "Add handler", "description": "..." },
      { "title": "Add repository method", "description": "..." }
    ]

Benefits:
*   Smaller prompts    
*   More accurate edits    
*   Atomic commits    
*   Better fixability

# 4.3 Sub‑Task Execution

`task_executor.py` handles:
*   Building prompts    
*   Calling OpenCode    
*   Applying edits    
*   Committing    
*   Retrying    
*   Storing memory
    
Each sub‑task is atomic and reproducible.

# 4.4 Multi‑Pass Refinement

Each sub‑task can run multiple passes:

    pass 1 → initial code
    pass 2 → fix missing imports
    pass 3 → fix TypeScript errors
    pass 4 → fix .NET namespaces    

This dramatically improves quality and reduces FixLoop load.

# 4.5 Task Memory

`task_memory.py` stores:
*   Changed files    
*   Errors    
*   Fixes    
*   Context
    
Later tasks use this to improve accuracy and consistency.

# 4.6 PR Enhancement

`pr_enhancer.py` adds:
*   Task summary    
*   Sub‑task summary    
*   Fix logs    
*   Build/test logs    
*   Changed file list    
*   Architecture impact summary
    
This makes PRs readable, reviewable, and auditable.

[<< Overview](../../README.md)
 | 
[<< Module 3: Build, Test, Lint, Format & Auto‑Fix Validation](./4-module-3.md)
 | 
[Architecture Overview >>](./6-architecture-overview.md)
