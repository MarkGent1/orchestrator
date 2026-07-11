# 1.2.4 Phase 1 — Skill Context Profiles

# What is a Skill Context Profile

A **Skill Context Profile** defines:

*   **What context the skill receives**    
*   **How that context is shaped**    
*   **How that context is compressed**    
*   **What boundaries are enforced**    
*   **What the skill must never see**    
*   **What the skill must always see**    
*   **How context is rehydrated on resume**
    
It is the _contract_ between your orchestrator and each skill.

# Skill Context Profile 1 — Planner

### **Purpose:** Convert work item → plan

### **Receives:**

*   Work item title    
*   Work item description    
*   Repo type    
*   Module map (compressed)    
*   High-level architecture rules    

### **Shaping:**

*   Distill work item into bullet points    
*   Compress module map into a list of module names    
*   Include only top-level architecture rules    
*   Exclude all code    

### **Must NOT see:**

*   File contents    
*   Tests    
*   Errors    
*   Diffs    
*   Build logs    

### **Rehydration:**

*   Work item from ADO MCP    
*   Repo type from workspace    
*   Module map from workspace    

# Skill Context Profile 2 — Decomposer

### **Purpose:** Convert task → subtasks

### **Receives:**

*   Task title    
*   Task description    
*   Architecture rules relevant to the task    
*   Repo type    

### **Shaping:**

*   Compress task description    
*   Include only architecture rules relevant to the module    
*   Exclude implementation details    

### **Must NOT see:**

*   Code    
*   Tests    
*   Errors    
*   Diffs    

### **Rehydration:**

*   Task context from RunState    
*   Architecture rules from enforcer    

# Skill Context Profile 3 — Executor

### **Purpose:** Generate file edits

### **Receives:**

*   Relevant file slice    
*   Relevant test slice    
*   Subtask description    
*   Architecture rule relevant to the file    
*   Strict JSON instructions    

### **Shaping:**

*   Slice file to relevant region    
*   Include structural anchors (namespace, class, method)    
*   Include only tests related to the file    
*   Include only the architecture rule relevant to the file    
*   Include strict JSON output contract    

### **Must NOT see:**

*   Full plan    
*   Full work item    
*   Unrelated files    
*   Unrelated tests    
*   Unrelated errors    
*   Build logs    

### **Rehydration:**

*   File contents from temp workspace    
*   Subtask from RunState    
*   Architecture rule from enforcer    

# Skill Context Profile 4 — FixLoop

### **Purpose:** Repair errors

### **Receives:**

*   Actionable error slice    
*   Relevant file slice    
*   Architecture rule relevant to the file    
*   Strict JSON instructions    

### **Shaping:**

*   Extract only the failing test or build error    
*   Slice file to the region causing the error    
*   Include only the architecture rule relevant to the violation    
*   Include strict JSON output contract    

### **Must NOT see:**

*   Full logs    
*   Unrelated errors    
*   Full repo    
*   Plan    
*   Tasks    

### **Rehydration:**

*   Error slice from validator    
*   File slice from workspace    
*   Architecture rule from enforcer    

# Skill Context Profile 5 — Validator

### **Purpose:** Build + test + architecture check

### **Receives:**

*   Build output (compressed)    
*   Test output (compressed)    
*   Architecture violations    
*   Repo type    

### **Shaping:**

*   Extract actionable errors    
*   Compress logs    
*   Include only relevant architecture violations    

### **Must NOT see:**

*   Plan    
*   Tasks    
*   Subtasks    
*   File contents    

### **Rehydration:**

*   Build/test output from real tools    
*   Architecture violations from enforcer    

# Skill Context Profile 6 — ArchitectureEnforcer

### **Purpose:** Enforce Clean Architecture

### **Receives:**

*   Module map    
*   File contents    
*   Repo type    

### **Shaping:**

*   Compress module map    
*   Slice file to relevant imports/usings    
*   Extract dependency graph    

### **Must NOT see:**

*   Plan    
*   Tasks    
*   Errors    

### **Rehydration:**

*   Module map from workspace    
*   File contents from workspace    

# Skill Context Profile 7 — PR Enhancer

### **Purpose:** Generate PR summary

### **Receives:**

*   Plan    
*   Task memory    
*   Validation summary    
*   Changed files list    

### **Shaping:**

*   Compress plan    
*   Compress task memory    
*   Compress validation summary    
*   Include only file paths, not contents    

### **Must NOT see:**

*   Code    
*   Errors    
*   Architecture rules    

### **Rehydration:**

*   Plan from RunState    
*   Task memory from TaskMemory    
*   Validation summary from validator    

# Skill Context Profile 8 — RunState

### **Purpose:** Persist progress

### **Receives:**

*   Plan    
*   Tasks    
*   Subtasks    
*   Validation status    
*   PR URL    

### **Shaping:**

*   Store only metadata    
*   Exclude code    
*   Exclude errors    
*   Exclude architecture rules    

### **Must NOT see:**

*   File contents    
*   Errors    
*   Architecture rules    

### **Rehydration:**

*   JSON state file    

# The Skill Context Profile Matrix

Here’s the clean matrix:

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

This matrix is the **contract** your orchestrator will use to route context correctly.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Current Orchestrator Skill Registry](./11-phase1-current-skill-registry.md)
 | 
[Phase 1 — Skill Routing >>](./13-phase1-skill-routing.md)
