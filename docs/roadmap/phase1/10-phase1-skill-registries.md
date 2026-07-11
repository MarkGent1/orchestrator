# 1.2.2 Phase 1 — Skill Registries

# What a Skill Registry _is_

A **Skill Registry** is a single source of truth that defines:

*   what skills exist    
*   what each skill does    
*   what context it consumes    
*   what context it must not see    
*   which model it uses    
*   how reliable it is    
*   how it fails    
*   how it recovers    
*   how it composes with other skills
    
It is the **operating system** of your agentic environment.

# The Skill Registry Structure

Your registry will contain **Skill Definitions**, each with:

### 1. Name

Human-readable identifier.

### 2. Purpose

What problem the skill solves.

### 3. Inputs (Context Profile)

What context the skill is allowed to consume.

### 4. Boundaries

What context the skill must never see.

### 5. Model Profile

Which model(s) the skill uses.

### 6. Output Contract

What the skill must produce.

### 7. Reliability Strategy

Retry, strict mode, fallback, fixloop, etc.

### 8. Dependencies

Which other skills must run before/after.

### 9. Lifecycle Hooks

Before/after execution hooks.

### 10. Metadata

Cost, latency, context size, risk level.

This turns skills into **first‑class objects**.

Here’s a conceptual structure:

```
SKILL_REGISTRY = {
    "planner": {
        "purpose": "...",
        "inputs": [...],
        "boundaries": [...],
        "model": "...",
        "output": "...",
        "reliability": {...},
        "dependencies": [...],
        "lifecycle": {...},
        "metadata": {...},
    },
    "decomposer": { ... },
    "executor": { ... },
    "fixloop": { ... },
    "validator": { ... },
    "architecture_enforcer": { ... },
    "pr_enhancer": { ... },
    "run_state": { ... },
}
```

This registry becomes the **brain** of your agentic system.

Once you have a registry, you can build:

### ✔ Skill-aware context routing

Each skill automatically receives the correct context profile.

### ✔ Skill-aware model selection

Swap models per skill dynamically.

### ✔ Skill-aware reliability strategies

Strict JSON for executor, multi-step retry for fixloop, etc.

### ✔ Skill-aware logging

Each skill gets its own logs.

### ✔ Skill-aware metrics

Latency, cost, error rate per skill.

### ✔ Skill-aware orchestration

Dynamic pipelines based on skill dependencies.

### ✔ Multi-agent systems

Each skill becomes an agent.

### ✔ Agent supervision

Supervisor agent monitors skill performance.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — What is a Skill in an Agentic System](./9-phase1-skill-systems.md)
 | 
[Phase 1 — Current Orchestrator Skill Registry >>](./11-phase1-current-skill-registry.md)
