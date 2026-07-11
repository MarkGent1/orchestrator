# 1.2.3 Phase 1 — Current Orchestrator Skill Registry

Below is the registry for your orchestrator’s current skills.

# Skill: Planner

 * **Purpose:** Convert work item → plan
 * **Inputs:** Work item, repo type, module map
 * **Boundaries:** No code, tests, errors
 * **Model:** Planning model (Sonnet)
 * **Output:** `{ tasks: [...] }`
 * **Reliability:** Retry on malformed plan
 * **Dependencies:** None
 * **Lifecycle:** Pre: load work item, Post: persist plan

# Skill: Decomposer

 * **Purpose:** Convert task → subtasks
 * **Inputs:** Task, architecture rules
 * **Boundaries:** No code, tests
 * **Model:** Decomposition model (GPT‑mini)
 * **Output:** `[ { title, description } ]`
 * **Reliability:** Persist once, never recompute
 * **Dependencies:** Planner
 * **Lifecycle:** Pre: load task, Post: store subtasks

# Skill: Executor

 * **Purpose:** Generate file edits
 * **Inputs:** File slice, test slice, subtask, architecture rule
 * **Boundaries:** No plan, no unrelated files
 * **Model:** Execution model (Haiku)
 * **Output:** JSON file edits
 * **Reliability:** Strict JSON fallback + retry
 * **Dependencies:** Decomposer
 * **Lifecycle:** Pre: slice file, Post: validate JSON

# Skill: FixLoop

 * **Purpose:** Repair errors
 * **Inputs:** Error slice, file slice
 * **Boundaries:** No unrelated errors, no full logs
 * **Model:** FixLoop model (Haiku)
 * **Output:** corrected JSON file edits
 * **Reliability:** Multi-step retry
 * **Dependencies:** Executor
 * **Lifecycle:** Pre: extract error, Post: re-run validator

# Skill: Validator

 * **Purpose:** Build + test + architecture check
 * **Inputs:** Build output, test output, architecture rules
 * **Boundaries:** No plan, no tasks
 * **Model:** None (real tools)
 * **Output:** pass/fail + error slice
 * **Reliability:** FixLoop integration
 * **Dependencies:** Executor
 * **Lifecycle:** Pre: build workspace, Post: error extraction

# Skill: ArchitectureEnforcer

 * **Purpose:** Enforce Clean Architecture
 * **Inputs:** Module map, file contents
 * **Boundaries:** No plan, no tasks
 * **Model:** None
 * **Output:** violations
 * **Reliability:** FixLoop integration
 * **Dependencies:** Executor
 * **Lifecycle:** Pre: scan modules, Post: violation report

# Skill: PR Enhancer

 * **Purpose:** Generate PR summary
 * **Inputs:** Plan, task memory, validation summary
 * **Boundaries:** No code, no errors
 * **Model:** Planning model (Sonnet)
 * **Output:** PR body
 * **Reliability:** Retry on malformed markdown
 * **Dependencies:** Validator
 * **Lifecycle:** Pre: gather memory, Post: open PR

# Skill: RunState

 * **Purpose:** Persist progress
 * **Inputs:** Plan, tasks, subtasks, validation, PR URL
 * **Boundaries:** No code, no errors
 * **Model:** None
 * **Output:** JSON state file
 * **Reliability:** Atomic writes
 * **Dependencies:** All skills
 * **Lifecycle:** Pre: load state, Post: save state

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Skill Registries](./10-phase1-skill-registries.md)
 | 
[Phase 1 — Skill Context Profiles >>](./12-phase1-skill-context-profiles.md)
