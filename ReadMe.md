# Orchestrator — Autonomous SDLC Engine

This orchestrator turns Work Items into:

 - feature branches
 - code changes
 - commits
 - build/test/lint/format validation
 - pull requests
 - ADO links

It is a full AI‑driven SDLC loop.

# Features

## Module 1 — Work Item Planning

 - Reads Work Item
 - Generates task plan

## Module 2 — Task Execution

 - Creates feature branch
 - Executes tasks
 - Applies file edits
 - Commits changes
 - Pushes branch
 - Opens PR
 - Links PR to Work Item

## Module 3 — Validation

 - Build
 - Test
 - Lint
 - Format
 - Auto‑fix
 - PR gating

## Module 4 — Multi‑Phase SDLC

 - Task decomposition
 - Sub‑task execution
 - Multi‑pass refinement
 - Task memory
 - PR enhancement

# Usage

```
python main.py <work_item_id> --repo <path_to_repo>
```

Example:

```
python main.py 151 --repo ../mav/mav-user-admin-poc
```

# Repo Support

## Backend (.NET)

 - Clean Architecture
 - Vertical slices
 - Domain/Application/Infrastructure
 - API controllers
 - EF Core
 - CQRS

## Frontend (React / Next.js / Node)

 - TypeScript
 - ESLint
 - Prettier
 - Next.js app router
 - React components
 - Hooks
 - API routes

# Architecture

```
orchestrator/
  main.py
  repo_type.py
  fix_loop.py
  validator.py

  # Backend
  backend_build.py
  backend_test.py

  # Frontend
  frontend_build.py
  frontend_test.py
  frontend_lint.py
  frontend_format.py

  # Module 4
  task_decomposer.py
  task_executor.py
  task_memory.py
  pr_enhancer.py
```

# Requirements

 - Python 3.10+
 - Node.js (for frontend repos)
 - .NET SDK (for backend repos)
 - MCP servers for GitHub + ADO
 - Anthropic API key

# License

Internal use only.