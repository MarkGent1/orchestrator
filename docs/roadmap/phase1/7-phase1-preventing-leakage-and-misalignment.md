# 1.1.6 Phase 1 — Preventing leakage and misalignment

**Goal:** Prevent skills from seeing context that would mislead them.

Context boundaries are not “nice to have.” 

They are **mandatory** for agentic correctness.

Think of them as the _firewalls_ between skills.

# Why Context Boundaries Matter

Every agentic failure you’ve ever seen falls into one of these categories:

### ❌ Overfeeding

Model sees too much context → hallucinates or over-edits.

### ❌ Underfeeding

Model sees too little context → produces incomplete or incorrect edits.

### ❌ Misfeeding

Model sees the wrong context → violates architecture or breaks tests.

### ❌ Cross-contamination

Context from one skill leaks into another → misaligned behaviour.
Context boundaries prevent all four.

# The Golden Rule of Context Boundaries

> **Each skill must only see the context required for its role — nothing more, nothing less.**

This is the foundation of agentic engineering.

Let’s define the boundaries for each skill in your orchestrator.

# Context Boundaries Per Skill

## Planner (WorkItemPlanner)

### MUST SEE

*   work item    
*   repo type    
*   module map    
*   high-level architecture rules    

### MUST NOT SEE

*   code    
*   tests    
*   errors    
*   diffs    
*   file contents    
*   build logs    

### WHY

Planner must think strategically, not tactically.
If it sees code, it will plan based on implementation instead of intent.

## Decomposer (TaskDecomposer)

### MUST SEE

*   task description    
*   architecture rules    
*   repo type    

### MUST NOT SEE

*   code    
*   tests    
*   errors    
*   diffs    
*   file contents    

### WHY

Decomposer must break down _intent_, not implementation.
If it sees code, it will generate subtasks based on the current implementation instead of the desired change.

## Executor (SubtaskExecutor)

### MUST SEE

*   relevant file slice    
*   relevant test slice    
*   subtask description    
*   architecture rule relevant to the file    
*   strict JSON instructions    

### MUST NOT SEE

*   full work item    
*   full plan    
*   unrelated files    
*   unrelated tests    
*   unrelated errors    
*   build logs    
*   architecture rules for other modules    

### WHY

Executor must focus on the exact code it’s editing.
If it sees the plan or unrelated files, it will over-edit or hallucinate.

## FixLoop (Error Repair Agent)

### MUST SEE

*   actionable error slice    
*   relevant file slice    
*   relevant architecture rule    
*   strict JSON instructions    

### MUST NOT SEE

*   full build logs    
*   full test suite    
*   full repo    
*   plan    
*   tasks    
*   unrelated errors    

### WHY

FixLoop must focus on the specific failure.
If it sees unrelated errors, it will fix the wrong thing.

## Validator (BuildTestValidator)

### MUST SEE

*   build output    
*   test output    
*   architecture violations    
*   repo type    

### MUST NOT SEE

*   plan    
*   tasks    
*   subtasks    
*   file contents    

### WHY

Validator must judge correctness, not intent.
If it sees the plan, it may bias validation.

## PR Enhancer

### MUST SEE

*   plan    
*   task memory    
*   validation summary    
*   changed files    

### MUST NOT SEE

*   code    
*   errors    
*   architecture rules    
*   file contents    

### WHY

PR Enhancer must summarise the work, not re-evaluate it.

## RunState (Memory)

### MUST SEE

*   plan    
*   tasks    
*   subtasks    
*   validation status    
*   PR URL    

### MUST NOT SEE

*   code    
*   errors    
*   file contents    
*   architecture rules    

### WHY

RunState must store _progress_, not _context_.

# Boundary Enforcement Techniques

Here are the engineering patterns you’ll use to enforce boundaries.

### 1. Context Bundles

Each skill receives a bundle containing only the allowed context.

### 2. Prompt Builders

Separate prompt builders per skill enforce isolation.

### 3. Context Routers

Route only the relevant context to each skill.

### 4. Context Slicers

Slice files, tests, and errors to relevant regions.

### 5. Context Profiles

Define what each skill is allowed to see.

### 6. Guardrails

Strict JSON, strict file-edit formats, strict error formats.

### 7. Memory Scopes

RunState stores only task-level context, not code.

# The Context Boundary Matrix

Here is the clean matrix showing what each skill can and cannot see:

```
    Skill              | Allowed Context                     | Forbidden Context
    -------------------|-------------------------------------|-------------------------------
    Planner            | Work item, repo type, modules       | Code, tests, errors, diffs
    Decomposer         | Task, architecture rules            | Code, tests, errors, diffs
    Executor           | File slice, test slice, subtask     | Plan, tasks, unrelated files
    FixLoop            | Error slice, file slice             | Full logs, unrelated errors
    Validator          | Build/test output, architecture     | Plan, tasks, code
    PR Enhancer        | Plan, memory, validation summary    | Code, errors, architecture
    RunState           | Plan, tasks, subtasks, PR URL       | Code, errors, architecture
```    

This matrix is the backbone of your agentic system.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Context boundaries](./6-phase1-context-boundaries.md)
 | 
[Phase 1 — The Agentic Context Graph >>](./8-phase1-agentic-context-graph.md)
