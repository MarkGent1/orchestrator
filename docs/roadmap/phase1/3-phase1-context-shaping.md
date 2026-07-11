# 1.1.2 Phase 1 — Context shaping

# Context Profiles (the “diet” each skill consumes)

Every skill in your orchestrator needs a different _profile_ of context.

Think of each skill as a specialist:
*   **Planner** → needs high‑level repo + work item context    
*   **Decomposer** → needs task context + architecture rules    
*   **Executor** → needs file-level context + strict JSON rules    
*   **FixLoop** → needs error context + local code context    
*   **Validator** → needs build/test context    
*   **PR Enhancer** → needs plan + task memory + diff summaries
    
If you give each skill _too much_ context → hallucinations
If you give each skill _too little_ context → wrong edits
If you give each skill the _wrong_ context → broken architecture

### What to aim for

A **context profile** per skill:

```
    Planner:           global + work item + repo type
    Decomposer:        global + task + architecture rules
    Executor:          local + micro + strict JSON
    FixLoop:           error + local + micro
    Validator:         build/test + architecture
    PR Enhancer:       plan + memory + validation summary
``` 

This is how you make each skill behave like a specialist.

# Context Isolation (preventing leakage)

Context leakage is when a skill sees information it shouldn’t.

Examples:
*   Executor sees the entire work item → produces irrelevant edits    
*   FixLoop sees the whole repo → misinterprets errors    
*   Planner sees file-level details → overfits the plan    
*   Decomposer sees code → decomposes based on implementation instead of intent    

### The rule

**Each skill should only see the context it needs to perform its role.**

### How you enforce isolation

*   separate prompt builders per skill    
*   separate context bundles per skill    
*   separate memory scopes per skill    
*   separate guardrails per skill
    
The orchestrator already does this implicitly - now we need to formalise it.

# Context Compression (feeding small models without losing meaning)

We’re using:
*   Claude Sonnet → large context    
*   Claude Haiku → small context    
*   GPT‑mini → very small context
    
Each model needs a different compression strategy.

### Compression techniques

*   semantic summaries
*   bullet-point distillation
*   architecture rule extraction
*   file-level slicing
*   diff slicing
*   error slicing
*   task title compression
*   subtask compression

### Example

Instead of giving the executor:

```
Full file + full test suite + full architecture rules + full plan
```

You give it:

```
Relevant file
Relevant test
Relevant architecture rule
Relevant subtask description
Strict JSON instructions
```

This is context shaping.

# Context Routing (sending the right context to the right skill)

This is where hierarchical context becomes dynamic.

### Routing examples in your orchestrator

*   Planner → gets work item + repo type    
*   Decomposer → gets task + architecture rules    
*   Executor → gets file + subtask    
*   FixLoop → gets error + file    
*   Validator → gets build/test output    
*   PR Enhancer → gets plan + memory    

### Routing rules

*   Global context → always available    
*   Task context → only for planning/decomposition    
*   Local context → only for execution/fixloop    
*   Micro context → only for execution/fixloop    
*   Memory context → only for PR enhancement
    
This is how you prevent skills from stepping on each other.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Hierarchical context design](./2-phase1-hierarchial-context-design.md)
 | 
[Phase 1 — Context Compression >>](./4-phase1-context-compression.md)
