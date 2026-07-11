# 1.1.5 Phase 1 — Context boundaries

# Context Boundaries (what must never be included)

This is where you prevent agentic failure.

### ❌ Executor must never see:

*   full work item    
*   full plan    
*   full repo
*   unrelated files    
*   unrelated tests    
*   unrelated errors    

### ❌ FixLoop must never see:

*   full repo    
*   unrelated errors    
*   unrelated tasks    

### ❌ Planner must never see:

*   file contents    
*   diffs    
*   errors    
*   architecture violations    

### ❌ Decomposer must never see:

*   implementation details    
*   code    
*   tests
    
These boundaries prevent hallucinations and misaligned edits.

# Context Shaping in Practice (your orchestrator)

Let’s map your orchestrator’s skills to shaped context.

### ✔ Planner

**Context:**
*   work item    
*   repo type    
*   architecture rules (high-level)    
*   module map
    
**Shaping:**
*   compress work item    
*   exclude code    
*   exclude tests    
*   exclude errors    

### ✔ Decomposer

**Context:**
*   task    
*   architecture rules    
*   repo type
    
**Shaping:**
*   exclude code    
*   exclude tests    
*   exclude errors    
*   compress task description    

### ✔ Executor

**Context:**
*   file contents    
*   subtask description    
*   architecture rules (local)    
*   strict JSON instructions
    
**Shaping:**
*   slice file to relevant region    
*   include only relevant tests    
*   include only relevant architecture rule    
*   exclude global plan    
*   exclude unrelated files    

### ✔ FixLoop

**Context:**
*   error message    
*   file contents    
*   architecture rule    
*   strict JSON instructions
    
**Shaping:**
*   slice error to relevant part    
*   slice file to relevant region    
*   exclude plan    
*   exclude tasks    
*   exclude unrelated errors    

### ✔ Validator

**Context:**
*   build output    
*   test output    
*   architecture violations
    
**Shaping:**
*   compress logs    
*   extract actionable errors    
*   exclude code    
*   exclude plan    

### ✔ PR Enhancer

**Context:**
*   plan    
*   task memory    
*   validation summary    
*   changed files
    
**Shaping:**
*   compress memory    
*   compress plan    
*   exclude code    
*   exclude errors

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Context rehydration](./5-phase1-context-rehydration.md)
 | 
[Phase 1 — Preventing leakage and misalignment >>](./7-phase1-preventing-leakage-and-misalignment.md)
