# 1.1.1 Phase 1 — Hierarchical context design

Think of context as **the working memory of your agentic system**. Hierarchical context is how you structure that memory so the agent always sees:

*   the right information    
*   at the right time    
*   in the right shape    
*   with the right boundaries

This is how you make an agent behave like a senior engineer instead of a confused autocomplete.

Four layers every Agentic system needs:

# Global Context (The “world” the agent lives in)

This is the context that defines the _environment_ the agent operates in.

### Examples in your orchestrator

*   repo type (backend / frontend / fullstack)    
*   architecture rules (Clean Architecture Enforcer)    
*   model configuration (planning, decomposition, execution, fixloop)    
*   MCP capabilities (ADO, GitHub, Azure)    
*   workspace structure (module map, temp workspace)    
*   global constraints (JSON-only output, file-edit-only output)    

### Purpose

Global context tells the agent:

> “This is the world you’re working in. These are the rules. These are the tools. These are the constraints.”

### Why it matters

Without global context:
*   agents hallucinate architecture    
*   agents violate repo boundaries    
*   agents generate invalid diffs    
*   agents produce wrong file paths    
*   agents misunderstand the repo type    

### What to master

*   designing global context schemas    
*   injecting global context into prompts    
*   enforcing global context boundaries    
*   compressing global context for small models    
*   rehydrating global context on resume    

# Task Context (The “mission” the agent is executing)

This is the context that defines the _goal_.

### Examples in your orchestrator

*   work item title    
*   work item description    
*   task list    
*   subtask list    
*   decomposition metadata    
*   run_state plan    
*   branch name    
*   PR metadata    

### Purpose

Task context tells the agent:

> “This is the mission. These are the steps. This is where we are in the plan.”

### Why it matters

Without task context:
*   agents forget the goal    
*   agents generate irrelevant edits    
*   agents repeat completed work    
*   agents lose track of subtasks    
*   agents break the plan on resume    

### What to master

*   designing task context trees    
*   storing task context in RunState    
*   shaping task context for planning vs execution    
*   compressing task context for small models    
*   rehydrating task context on resume    

# Local Context (The “workspace” the agent is editing)

This is the context that defines the _immediate working area_.

### Examples in your orchestrator

*   file contents    
*   diffs    
*   directory structure    
*   module boundaries    
*   architecture rules for the module    
*   test files related to the code    
*   build errors    
*   test failures    

### Purpose

Local context tells the agent:

> “This is the exact code you’re editing. These are the constraints. These are the related files.”

### Why it matters

Without local context:
*   agents hallucinate code    
*   agents break architecture    
*   agents misplace files    
*   agents generate invalid imports    
*   agents misunderstand dependencies    

### What to master

*   designing local context bundles    
*   shaping local context for file-edit models    
*   extracting local context from the workspace    
*   compressing local context for small models    
*   routing local context to the correct skill    

# Micro Context (The “moment-to-moment” details)

This is the context that defines the _specific action_ the agent is taking.

### Examples in your orchestrator

*   the exact prompt for the file-edit    
*   the strict JSON instructions    
*   the specific error message in fixloop    
*   the specific test failure    
*   the specific architecture violation    
*   the specific diff being applied    

### Purpose

Micro context tells the agent:

> “This is the exact thing you need to do right now.”

### Why it matters

Without micro context:
*   agents produce vague edits    
*   agents produce invalid JSON    
*   agents misinterpret errors    
*   agents fail fixloops    
*   agents produce incomplete diffs    

### What to master

*   designing micro context prompts    
*   shaping micro context for strict JSON    
*   extracting micro context from errors    
*   routing micro context to fixloop    
*   validating micro context outputs    

# The Hierarchical Context Pyramid

Here’s the full structure:

```
                    ┌────────────────────────────────┐
                    │        GLOBAL CONTEXT          │
                    │  (repo, architecture, tools)   │
                    └────────────────────────────────┘
                              ▲
                              │
                    ┌────────────────────────────────┐
                    │         TASK CONTEXT           │
                    │ (plan, tasks, subtasks, state) │
                    └────────────────────────────────┘
                              ▲
                              │
                    ┌────────────────────────────────┐
                    │        LOCAL CONTEXT           │
                    │ (files, modules, diffs, tests) │
                    └────────────────────────────────┘
                              ▲
                              │
                    ┌────────────────────────────────┐
                    │        MICRO CONTEXT           │
                    │ (prompt, error, fixloop)       │
                    └────────────────────────────────┘
```  

Each layer feeds the one below it.
Each layer constrains the one below it.
Each layer shapes the one below it.
This is how to build agents that behave like senior engineers.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Core Agent Foundations](./1-phase1-overview.md)
 | 
[Phase 1 — Context shaping >>](./3-phase1-context-shaping.md)
