# 1.2.1 Phase 1 — What is a Skill in an Agentic System

**Goal:** Turn your agentic system into a coordinated team of specialists, each with its own role, context, boundaries, and behaviour.

# What is a “Skill” in an Agentic System?

A **skill** is not a model. A skill is a **capability** with:
*   a clear purpose    
*   a defined context profile    
*   strict boundaries    
*   a specific prompt style    
*   a specific model choice    
*   a specific output format    
*   a specific failure mode    
*   a specific retry strategy
    
A skill is a _unit of behaviour_.
Your orchestrator already treats skills this way — now we make it explicit.

# The Six Dimensions of a Skill

Every skill in your system should be defined by these six dimensions:

### 1. Purpose

What problem does this skill solve?

### 2. Inputs

What context does it consume?

### 3. Outputs

What does it produce?

### 4. Boundaries

What must it never see?

### 5. Model Profile

Which model is best for this skill?

### 6. Reliability Strategy

How does it handle failure?

# Our Current Skill System

## Planning Skill — _WorkItemPlanner_

 * **Purpose:** Turn a work item into a structured plan.
 * **Inputs:** Global context + work item.
 * **Outputs:** Plan → tasks.
 * **Boundaries:** No code, no tests, no errors.
 * **Model Profile:** Large reasoning model (Sonnet).
 * **Reliability:** Retry on malformed plan.

## Decomposition Skill — _TaskDecomposer_

 * **Purpose:** Break a task into subtasks.
 * **Inputs:** Task context + architecture rules.
 * **Outputs:** Subtask list.
 * **Boundaries:** No code, no tests.
 * **Model Profile:** Small reasoning model (GPT‑mini).
 * **Reliability:** Persist decomposition once; never recompute.

## Execution Skill — _SubtaskExecutor_

 * **Purpose:** Generate file edits.
 * **Inputs:** Local context + micro context.
 * **Outputs:** JSON file edits.
 * **Boundaries:** No plan, no unrelated files.
 * **Model Profile:** Small fast model (Haiku).
 * **Reliability:** Strict JSON fallback + retry.

## FixLoop Skill — _FixLoop_

 * **Purpose:** Repair errors.
 * **Inputs:** Error slice + file slice.
 * **Outputs:** Corrected file edits.
 * **Boundaries:** No unrelated errors, no full logs.
 * **Model Profile:** Small fast model (Haiku).
 * **Reliability:** Multi-step retry + strict JSON.

## Validation Skill — _BuildTestValidator_

 * **Purpose:** Verify correctness.
 * **Inputs:** Build/test output + architecture rules.
 * **Outputs:** Pass/fail + error slice.
 * **Boundaries:** No plan, no tasks.
 * **Model Profile:** No model — uses real tools.
 * **Reliability:** FixLoop integration.

## Architecture Enforcement Skill — _CleanArchitectureEnforcer_

 * **Purpose:** Ensure architecture rules are followed.
 * **Inputs:** Module map + file contents.
 * **Outputs:** Violations.
 * **Boundaries:** No plan, no tasks.
 * **Model Profile:** No model — static analysis.
 * **Reliability:** FixLoop integration.

## Memory Skill — _RunState + TaskMemory_

 * **Purpose:** Persist progress.
 * **Inputs:** Plan + tasks + subtasks + validation + PR.
 * **Outputs:** Rehydrated context.
 * **Boundaries:** No code, no errors.
 * **Model Profile:** No model — pure data.
 * **Reliability:** Atomic writes.

## Enhancement Skill — _PR Enhancer_

 * **Purpose:** Generate PR summary.
 * **Inputs:** Plan + memory + validation summary.
 * **Outputs:** PR body.
 * **Boundaries:** No code, no errors.
 * **Model Profile:** Large language model (Sonnet).
 * **Reliability:** Retry on malformed markdown.

# Skill Orchestration (the “agent pipeline”)

Your orchestrator already follows a pipeline:

```
    Planner → Decomposer → Executor → FixLoop → Validator → PR Enhancer
```  

This is a **skill graph**, not a linear pipeline.

Let’s draw it:

```
    Planner
      ↓
    Decomposer
      ↓
    Executor → FixLoop → Validator
      ↓
    PR Enhancer
```

This is the backbone of your agentic system.

# Skill Isolation (critical for correctness)

Each skill must be isolated:
*   separate prompt builder    
*   separate context profile    
*   separate model    
*   separate output format    
*   separate retry strategy
    
This prevents:
*   cross-contamination    
*   hallucinations    
*   over-editing    
*   misaligned behaviour
    
You’ve already implemented this implicitly — now we formalise it.

# Skill Specialisation (model selection per skill)

This is where you become a top agentic engineer.

Different skills need different models:
*   **Planning** → large reasoning    
*   **Decomposition** → small reasoning    
*   **Execution** → small fast    
*   **FixLoop** → small fast    
*   **PR Enhancement** → large expressive
    
This is why your orchestrator works so well.

# Skill Reliability (fixloops, retries, strict modes)

Each skill needs its own reliability strategy:
*   Planner → retry on malformed plan    
*   Decomposer → persist once    
*   Executor → strict JSON fallback    
*   FixLoop → multi-step retry    
*   Validator → fixloop integration    
*   PR Enhancer → markdown fallback
    
This is how you build agents that don’t break.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — The Agentic Context Graph](./8-phase1-agentic-context-graph.md)
 | 
[Phase 1 — Skill Registries >>](./10-phase1-skill-registries.md)
