# 1.1.7 Phase 1 — The Agentic Context Graph

# The Agentic Context Graph

The **real architecture** behind agentic systems: the **Context Graph**.

This is the blueprint that shows:
*   what each agent/skill _needs_    
*   what each agent/skill _must not see_    
*   how context _flows_ through the system    
*   how context is _compressed_ and _reshaped_    
*   how context is _rehydrated_ on resume    
*   how context _isolates_ skills so they don’t interfere with each other
    
A well‑designed context graph is the difference between:
*   an AI that “kind of works”    
*   and an AI that behaves like a coordinated team of senior engineers
    
Below is the full, structured, engineering‑grade context graph for your orchestrator — tailored to your architecture, your RunState, your MCP servers, your SDLC loop, and your agentic goals.

This is the **top‑level structure** of your agentic system.

```
GLOBAL CONTEXT
    ↓
TASK CONTEXT
    ↓
LOCAL CONTEXT
    ↓
MICRO CONTEXT
```

But that’s just the hierarchy. The **graph** shows how context _moves_ between skills.

# Nodes (the skills/agents in your system)

The orchestrator already has these nodes:

### Planning Agents

*   WorkItemPlanner    
*   TaskDecomposer    

### Execution Agents

*   SubtaskExecutor (file‑edit model)    
*   FixLoop (error‑repair model)    

### Validation Agents

*   BuildTestValidator    
*   ArchitectureEnforcer    

### Integration Agents

*   ADO MCP    
*   GitHub MCP    
*   Azure MCP (coming soon)    

### Memory Agents

*   RunState    
*   TaskMemory    

### Enhancement Agents

*   PR Enhancer
    
Each of these nodes consumes and produces context.

# Edges (context flows between nodes)

Here is the **actual context graph** for your orchestrator:

```
WorkItemPlanner
    ↑ global context
    ↓ task context
TaskDecomposer
    ↑ task context
    ↑ architecture rules
    ↓ subtask context
SubtaskExecutor
    ↑ subtask context
    ↑ local file context
    ↑ architecture rules
    ↑ strict JSON rules
    ↓ file edits
FixLoop
    ↑ error context
    ↑ local file context
    ↑ architecture rules
    ↓ corrected file edits
BuildTestValidator
    ↑ repo context
    ↑ architecture rules
    ↓ validation context
PR Enhancer
    ↑ plan context
    ↑ task memory
    ↑ validation context
ADO/GitHub/Azure MCP
    ↑ integration context
RunState
    ↔ task context
    ↔ subtask context
    ↔ validation context
TaskMemory
    ↔ execution context
```

This is the **full agentic context graph**.

# Context Layers (the “shape” of context at each stage)

## Layer 1 — Global Context

Used by:
*   Planner    
*   Decomposer    
*   Architecture Enforcer    
*   Validator
    
Contains:
*   repo type    
*   module map    
*   architecture rules    
*   model configuration    
*   MCP capabilities    
*   workspace structure
    
Never shown to:
*   Executor    
*   FixLoop

## Layer 2 — Task Context

Used by:
*   Planner    
*   Decomposer    
*   PR Enhancer    
*   RunState
    
Contains:
*   work item    
*   plan    
*   tasks    
*   subtasks    
*   branch name    
*   PR metadata
    
Never shown to:
*   Executor    
*   FixLoop    
*   Validator

## Layer 3 — Local Context

Used by:
*   Executor    
*   FixLoop    
*   Validator    
*   Architecture Enforcer
    
Contains:
*   file contents    
*   related tests    
*   module boundaries    
*   architecture rules    
*   diffs    
*   error logs
    
Never shown to:
*   Planner    
*   Decomposer

## Layer 4 — Micro Context

Used by:
*   Executor    
*   FixLoop
    
Contains:
*   strict JSON instructions    
*   specific subtask description    
*   specific error message    
*   specific diff
    
Never shown to:
*   Planner    
*   Decomposer    
*   PR Enhancer

# 5. Context Isolation Rules (critical for agent reliability)

These are the **hard boundaries** that prevent hallucinations.

### Planner must not see:

*   code    
*   tests    
*   errors    
*   diffs    

### Decomposer must not see:

*   code    
*   tests    
*   errors    
*   diffs    

### Executor must not see:

*   full work item    
*   full plan    
*   unrelated files    
*   unrelated tests    
*   unrelated errors    

### FixLoop must not see:

*   plan    
*   tasks    
*   unrelated errors    
*   unrelated files    

### Validator must not see:

*   plan    
*   tasks    
*   subtasks    

### PR Enhancer must not see:

*   code    
*   errors    
*   architecture rules
    
These boundaries are essential for agentic correctness.

# Context Compression Rules (for small models)

You’re using:
*   Claude Sonnet (large)    
*   Claude Haiku (small)    
*   GPT‑mini (very small)
    
Each needs different compression.

### Compression strategies

*   semantic summaries    
*   bullet-point distillation
*   slicing file to relevant region    
*   slicing error logs    
*   slicing architecture rules    
*   slicing test failures    
*   slicing diffs    
*   slicing task descriptions
    
This is how you feed small models without losing meaning.

# Context Rehydration Rules (for resume)

Your RunState enables:
*   plan rehydration    
*   task rehydration    
*   subtask rehydration    
*   validation rehydration    
*   PR rehydration
    
On resume, the context graph reconstructs:
*   global context → from repo    
*   task context → from RunState    
*   local context → from temp workspace    
*   micro context → from subtask
    
This is how your orchestrator survives crashes.

# The Final Context Graph

```
GLOBAL CONTEXT
    ↓
WorkItemPlanner → TASK CONTEXT → TaskDecomposer
    ↓                                 ↓
RunState ←——————————————— SUBTASK CONTEXT ———————————————→ TaskMemory
    ↓                                 ↓
LOCAL CONTEXT → ArchitectureEnforcer → SubtaskExecutor → MICRO CONTEXT
    ↓                                 ↓
Validator ←——————————————— FixLoop ———————————————→ File Edits
    ↓
PR Enhancer
    ↓
ADO/GitHub/Azure MCP
```

This is the architecture of a **real agentic system**.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Preventing leakage and misalignment](./7-phase1-preventing-leakage-and-misalignment.md)
 | 
[Phase 1 — What is a Skill in an Agentic System >>](./9-phase1-skill-systems.md)
