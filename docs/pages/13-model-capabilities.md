# 📘 Model Capabilities — Multi‑Model SDLC Architecture

This document describes the AI model strategy used by the Orchestrator.  
The system operates as a **multi‑agent, multi‑model SDLC engine**, with each phase powered by a model chosen specifically for its strengths.

---

# 🧠 Overview

The orchestrator uses **four specialised AI agents**, each backed by a different model:

| Phase            | Model               | Provider   | Purpose |
|------------------|---------------------|------------|---------|
| Planning         | Claude Sonnet 4.6   | Anthropic  | Deep reasoning, structured plans |
| Decomposition    | GPT‑5.4‑mini        | OpenAI     | Cheap, fast JSON arrays |
| Task Execution   | Claude Haiku 4.5    | Anthropic  | Fast, predictable code edits |
| FixLoop          | Claude Haiku 4.5    | Anthropic  | Minimal, safe fixes |

Model selection is dynamic and controlled by:

- `model_constants.py`  
- `model_selector.py`  
- `models.yaml`  
- CLI overrides  

This architecture ensures **speed, reliability, cost‑efficiency, and correctness** across the entire SDLC loop.

---

# 🧩 1. Planning Model — Claude Sonnet 4.6

### Purpose
Used for Work Item → Task planning.

### Why Sonnet?
- Exceptional long‑context reasoning  
- Produces structured, minimal, non‑overlapping plans  
- Very low hallucination rate  
- Ideal for understanding Work Item intent  

### Used In
- `WorkItemPlanner.plan_work_item()`

### Strengths
- Deep reasoning  
- High‑quality JSON  
- Excellent summarisation  
- Stable across large prompts  

---

# ⚙️ 2. Decomposition Model — GPT‑5.4‑mini

### Purpose
Breaks tasks into 2–6 actionable subtasks.

### Why GPT‑mini?
- Extremely fast  
- Extremely cheap  
- Produces clean JSON arrays  
- Perfect for lightweight decomposition  

### Used In
- `task_decomposer.decompose_task()`

### Strengths
- High‑speed JSON generation  
- Low cost  
- Predictable structure  

---

# ⚡ 3. Execution Model — Claude Haiku 4.5

### Purpose
Generates code edits for each subtask.

### Why Haiku?
- Very fast  
- Very stable JSON  
- Minimal hallucination  
- Ideal for iterative code generation  
- Perfect for multi‑commit SDLC loops  

### Used In
- `task_executor.execute_subtask()`

### Strengths
- Predictable file‑edit JSON  
- Strong code‑generation accuracy  
- Safe for repeated calls  

---

# 🔧 4. FixLoop Model — Claude Haiku 4.5

### Purpose
Self‑healing engine for build/test failures.

### Why Haiku?
FixLoop requires:

- Minimal edits  
- Strict JSON  
- High reliability  
- Zero hallucination  
- Fast turnaround  

Haiku is the best model for this job.

### Used In
- `FixLoop.attempt_fix()`  
- `BuildTestValidator._fix_and_retry()`

### Strengths
- Predictable JSON  
- Minimal diffs  
- Safe path handling  
- Excellent for targeted fixes  

---

# 🔌 Provider Resolution

Models are routed automatically based on prefix:

| Model Prefix | Provider     |
|--------------|--------------|
| `claude-*`   | Anthropic    |
| `gpt-*`      | OpenAI       |

Handled by:

```
resolve_provider(model)
```

---

# 🔁 Unified Call Layer

All model calls go through:

```
call_model()
call_model_json()
```

These route to:

 - call_opencode() / call_opencode_json() (Claude)
 - call_openai() / call_openai_json() (OpenAI)

This ensures:

 - consistent JSON extraction
 - consistent sanitization
 - consistent retry logic
 - consistent error handling

---

# 🧠 Dynamic Model Selection

The orchestrator chooses models dynamically based on:

 - SDLC phase
 - task type
 - repo type (backend/frontend)
 - FixLoop detection

Handled by:

```
select_model_for_planning()
select_model_for_decomposition()
select_model_for_task_execution()
select_model_for_fixloop()
```

---

# 🗂 Configuration

Models can be configured via:

1. models.yaml

Default model configuration.

2. CLI flags

Override defaults:

```
--planning-model claude-sonnet-4-6
--decomposition-model gpt-5.4-mini
--execution-model claude-haiku-4-5
--fixloop-model claude-haiku-4-5
```

3. model_constants.py

Global defaults.

# 🎯 Summary

The orchestrator uses:

 - Multiple AI models
 - Multiple providers
 - Dynamic routing
 - Unified call layer
 - Phase‑specific agents
 - Clean Architecture enforcement
 - Self‑healing FixLoop

This is a **true multi‑agent SDLC engine**, designed for reliability, speed, and correctness.

[<< Overview](../../README.md)
 | 
[<< How to Onboard New Repos](./12-onboard-new-repos.md)
