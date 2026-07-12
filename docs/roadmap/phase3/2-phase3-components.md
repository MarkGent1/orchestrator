# 3.1 Phase 3 — Components

### 1 Parallel Execution Engine

This is the first implementation step after the roadmap.

**Deliverables**
*   Worker pool (AsyncWorkerPool)
*   Subtask dependency graph
*   Parallel execution inside _execute_tasks()
*   Safe commit ordering
*   Safe RunState updates
*   Architecture‑safe concurrency

**Why this is first**
It gives immediate, measurable performance gains and is the foundation for multi‑agent coordination.

### 2 Agent Messaging Layer

Agents currently communicate only through SupervisorAgent.

Phase 3 introduces:

**Agent‑to‑Agent Messaging**
*   ExecutionAgent → ArchitectureAgent: “validate this path”
*   PR Agent → ExecutionAgent: “give me code slices”
*   FixLoopAgent → ExecutionAgent: “give me failing diff context”
*   DecompositionAgent → ArchitectureAgent: “suggest module placement”

**SupervisorAgent becomes a router**
Messages flow through a central bus:

```
SupervisorAgent
    ↳ routes messages
    ↳ enforces ordering
    ↳ handles failures
```

**Deliverables**
*   AgentMessage schema
*   MessageBus
*   inbox/outbox queues
*   SupervisorAgent routing logic

### 3 Multi‑Agent Reflection

Agents gain the ability to refine their own outputs.

**Examples**
*   PR Agent generates PR → PR Agent refines PR → PR Agent finalises PR
*   ArchitectureAgent flags a violation → ExecutionAgent proposes fix → ArchitectureAgent validates fix
*   DecompositionAgent proposes subtasks → ExecutionAgent suggests merging/splitting → DecompositionAgent refines

**Deliverables**
*   Reflection loop API
*   Reflection policies per agent
*   SupervisorAgent reflection orchestration

### 4 Observability & Metrics

Add a metrics layer:

**Per‑agent metrics**
*   latency
*   token usage
*   retries
*   success/failure
*   architecture violations
*   fixloop attempts

**Timeline**
A chronological log of:

*   planning
*   decomposition
*   execution
*   validation
*   PR creation

**Deliverables**
*   AgentMetrics
*   MetricsCollector
*   timeline JSON
*   optional dashboard UI

### 5 Developer Dashboard

A lightweight dashboard (CLI or web) showing:

**Views**
*   Work Item Summary
*   Plan → Subtasks → Commits
*   Architecture Map
*   Module Map
*   Validation Summary
*   FixLoop Attempts
*   PR Summary
*   Agent Timeline
*   Metrics

**Deliverables**
*   dashboard/ module
*   JSON → HTML renderer
*   optional FastAPI server

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 3 — Multi‑Agent Coordination, Parallelism & Intelligence](./1-phase3-overview.md)
 | 
[Phase 3 — Folder Structure >>](./3-phase3-folder-structure.md)
