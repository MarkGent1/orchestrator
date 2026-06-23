# 2. Module 2: Branch + PR Automation

# 2.1. Overview

Module 2 extends the orchestrator beyond planning. It now:

*   Reads a Work Item    
*   Generates a task plan    
*   Creates a feature branch    
*   Iterates through each task    
*   Calls OpenCode (Claude) to generate file edits    
*   Applies edits safely    
*   Commits each task atomically    
*   Pushes the branch    
*   Opens a PR    
*   Links the PR to the Work Item
    
This is the **AI developer loop**.

# 2.2. Orchestrator Structure (Updated)

```
orchestrator/
  main.py
  work_item_planning.py
  fix_loop.py
  validator.py
  file_editing.py
  git_workflow.py
  github_mcp_client.py
  ado_mcp_client.py
  backend_build.py
  backend_test.py
  frontend_build.py
  frontend_test.py
  frontend_lint.py
  frontend_format.py
  task_decomposer.py
  task_executor.py
  task_memory.py
  pr_enhancer.py
  architecture/
    enforcement.py
  utils/
    path_normalization.py
    repo_scanner.py
    tree_visualiser.py
    copy_repo.py
``` 

### ✔ `fix_loop.py`

Self‑healing engine with:
*   Clean Architecture enforcement    
*   Safe path validation    
*   Minimal diff philosophy    
*   No destructive edits    
*   No JSON corruption    
*   No csproj rewrites unless required

### ✔ `validator.py`

Runs:
*   Build    
*   Tests    
*   Lint/format (frontend)    
*   FixLoop on failure    
*   Retries until green    

### ✔ `file_editing.py`

Safe file writer:
*   No JSON decoding    
*   No escape corruption    
*   No hallucinated folders    
*   No overwrites outside module boundaries    

### ✔ `git_workflow.py`

Handles:
*   Branch creation    
*   Commit per subtask    
*   Push    
*   PR creation    

### ✔ `pr_enhancer.py`

Generates:
*   PR summary    
*   Plan summary    
*   Task breakdown    
*   Changed files list

# 2.3. Module 2 Flow

### 1. CLI Entry

```
python main.py <id> --repo <path>
```

### 2. Fetch Work Item

Via ADO MCP.

### 3. Generate Plan

Module 1.

### 4. Create Feature Branch

`feature/<id>-<slug>`

### 5. Task Loop

For each task:
1.  Decompose into subtasks    
2.  Build repo‑aware prompt    
3.  Call OpenCode    
4.  Apply edits safely    
5.  Commit    
6.  Run build + tests    
7.  FixLoop if needed    

### 6. Push Branch

Via GitHub MCP.

### 7. Open PR

With enhanced description.

### 8. Link PR to Work Item

Via ADO MCP.
    
# 2.4. Smart AI Code Generation

The orchestrator now:
*   Reads the repo tree    
*   Detects modules    
*   Enforces Clean Architecture    
*   Applies minimal diffs    
*   Avoids destructive rewrites    
*   Generates atomic commits    
*   Produces reproducible changes
    
This is now **production‑grade AI development**.

# 2.5. Repo-Agnostic Architecture

### Backend (.NET)

*   Clean Architecture    
*   Vertical slices    
*   Controllers, Services, Models    
*   EF Core    
*   CQRS    
*   Unit + Integration tests    

### Frontend (React/Next.js)

*   TypeScript    
*   ESLint    
*   Prettier    
*   App Router    
*   API routes

# 2.6. Getting Started Guide

```
python main.py <work_item_id> --repo <path_to_repo>
```

Temp workspace:

```
<repo>/.orchestrator-tmp/
```

Everything happens there until PR creation.

[<< Overview](../../README.md)
 | 
[<< Module 1: Work Item + Plan + Tasks](./2-module-1.md)
 | 
[Module 3: Build, Test, Lint, Format & Auto‑Fix Validation >>](./4-module-3.md)
