# 5. Architecture Overview

The orchestrator is built as a **modular, deterministic, repo‑agnostic SDLC engine**. It combines:

*   Azure DevOps MCP
*   GitHub MCP
*   Multi‑model AI (Claude + OpenAI)
*   Clean Architecture enforcement  
*   A temp‑workspace execution model
*   A self‑healing FixLoop
*   A multi‑phase SDLC pipeline
    
This page describes the full architecture.

## 5.1 Multi‑Agent SDLC Flow (Claude + OpenAI)

```
User CLI
  python main.py <work_item_id>
        |
        v
Orchestrator (main.py)
        |
        v
+---------------------------+
|  Planning Agent           |
|  Model: Claude Sonnet     |
|  File: work_item_planning |
+---------------------------+
        |
        v
+---------------------------+
|  Decomposition Agent      |
|  Model: GPT‑5.4‑mini      |
|  File: task_decomposer    |
+---------------------------+
        |
        v
+---------------------------+
|  Execution Agent          |
|  Model: Claude Haiku      |
|  File: task_executor      |
+---------------------------+
        |
        v
+---------------------------+
|  Build/Test Validator     |
|  Tools: dotnet / npm      |
|  File: validator          |
+---------------------------+
        |
   if failure
        v
+---------------------------+
|  FixLoop Agent            |
|  Model: Claude Haiku      |
|  File: fix_loop           |
+---------------------------+
        |
        v
+---------------------------+
|  Git + PR Automation      |
|  GitHub MCP / GitWorkflow |
+---------------------------+
        |
        v
ADO Work Item linked to PR
```

## 5.2 Module Overview

### Module 1 — Work Item Planning

*   Reads Work Item    
*   Validates quality    
*   Generates plan    
*   Creates child tasks    
*   Adds comments    
*   Updates Work Item state    

### Module 2 — AI Developer Loop (GPT‑mini + Claude Haiku)

*   Creates feature branch    
*   Decomposes tasks (default: GPT‑mini)
*   Generates code edits (default: Claude Haiku)
*   Applies edits safely    
*   Commits per subtask    
*   Enhances PR    
*   Links PR to Work Item    

### Module 3 — Validation + FixLoop

*   Build    
*   Test    
*   Lint    
*   Format    
*   Auto‑fix    
*   Retry    
*   Only push if green    

### Module 4 — Multi‑Phase SDLC Loop

*   Task decomposition    
*   Sub‑task execution    
*   Multi‑pass refinement    
*   Task memory    
*   PR enhancement    

## 5.3 Temp Workspace Architecture

All code generation, builds, tests, and fixes happen inside:

    <repo>/.orchestrator-tmp/

This ensures:
*   Your real repo is never corrupted    
*   FixLoop cannot break your working tree    
*   All changes are validated before PR creation    

## 5.4 FixLoop Architecture

FixLoop is a **self‑healing engine**:

    Error → FixLoop → Edits → Apply → Rebuild → Retest → Repeat
    
It includes:
*   Clean Architecture enforcement    
*   Safe path validation    
*   Minimal diff philosophy    
*   No destructive edits    
*   No JSON corruption    
*   No hallucinated folders    
*   No csproj rewrites unless required    

## 5.5 Clean Architecture Enforcement

The orchestrator enforces:
*   No new modules    
*   No moving files across modules    
*   Only allowed folders inside modules    
*   Strict naming conventions    
*   Path validation before applying edits
    
This prevents AI from “inventing” architecture.

## 5.6 File Structure (Final)

    orchestrator/
      main.py
      validator.py
      fix_loop.py
      file_editing.py
    
      # Work Item Planning
      work_item_planning.py
      ado_mcp_client.py
    
      # GitHub + Git
      github_mcp_client.py
      git_workflow.py
      pr_enhancer.py
    
      # Task Execution
      task_decomposer.py
      task_executor.py
      task_memory.py
    
      # Backend
      backend_build.py
      backend_test.py
    
      # Frontend
      frontend_build.py
      frontend_test.py
      frontend_lint.py
      frontend_format.py
    
      # Architecture Enforcement
      architecture/
        enforcement.py
    
      # Utilities
      utils/
        path_normalization.py
        repo_scanner.py
        tree_visualiser.py
        copy_repo.py
    
## 5.7 End‑to‑End Flow Diagram

```
Work Item → Plan → Tasks → Branch → Sub‑Tasks → Edits → Commit → Build → Test → FixLoop → Push → PR → Link → Done
```

## 5.8 Multi‑Agent SDLC Sequence Diagram

![5.8.png](../images/5.8.png)

[<< Overview](../../README.md)
 | 
[<< Module 4: Multi‑Task, Multi‑Phase, Multi‑Commit SDLC Loop](./5-module-4.md)
 | 
[FixLoop Deep Dive >>](./7-fixloop-deep-dive.md)
