# 🚀 Orchestrator — Autonomous SDLC Engine

**AI‑driven Work Item → Branch → Code → Build/Test → PR automation**

This orchestrator performs a **full end‑to‑end SDLC loop** using:

 * Azure DevOps Work Items
 * GitHub repositories
 * Clean Architecture enforcement
 * AI‑generated code changes
 * Automated build/test validation
 * Self‑healing FixLoop
 * Automated PR creation + linking

It operates entirely inside a **temporary workspace**, ensuring your real repo stays clean until the PR is created.

# ✨ What It Does

Given a Work Item ID, the orchestrator:

 * Reads the Work Item
 * Generates a task plan
 * Creates a feature branch
 * Executes tasks + subtasks
 * Generates code edits via AI
 * Applies edits safely
 * Runs build + tests
 * Auto‑fixes failures using FixLoop
 * Repeats until everything is green
 * Pushes the branch
 * Opens a Pull Request
 * Links the PR to the Work Item

This is a fully autonomous SDLC engine.

# 🧠 Core Capabilities

## 1. Work Item Planning

 * Reads ADO Work Item
 * Extracts title, description, acceptance criteria
 * Generates a structured task plan
 * Validates Work Item quality
 * Adds comments back to ADO

## 2. Task Execution

 * Creates feature branch
 * Decomposes tasks into subtasks
 * Executes subtasks using AI
 * Applies file edits inside a temp workspace
 * Commits changes per subtask
 * Pushes branch
 * Opens PR
 * Enhances PR description

## 3. Build/Test Validation (Self‑Healing)

 * Runs backend or frontend build
 * Runs unit, integration, and component tests
 * Runs lint/format (frontend)
 * If anything fails → FixLoop kicks in
 * FixLoop generates targeted file edits
 * Edits are validated by Clean Architecture rules
 * Edits are applied safely
 * Build/test reruns
 * Loop continues until green or attempts exhausted

## 4. Clean Architecture Enforcement

For backend repos:

 * Only modifies files inside existing modules
 * Only allowed folders: Controllers, Models, DTOs, Services, Interfaces, Setup, Extensions
 * No new modules
 * No moving files across modules
 * No rewriting architecture
 * Strict naming conventions enforced

This prevents AI from “hallucinating” new architecture.

## 🛠️ How It Works Internally

### Temporary Workspace

The orchestrator copies your repo into:

```
<repo>/.orchestrator-tmp/
```

All code generation, builds, tests, and fixes happen **inside the temp workspace**.
Your real repo is untouched until the PR is created.

### FixLoop (Self‑Healing Engine)

FixLoop:

 * Reads build/test errors
 * Generates minimal, safe file edits
 * Validates paths with Clean Architecture rules
 * Applies edits
 * Rebuilds + retests
 * Repeats until fixed

FixLoop now includes:

 * Safe path resolution
 * No JSON corruption
 * No destructive overwrites
 * No csproj edits unless required
 * No Program.cs rewrites unless error demands it
 * Minimal diff philosophy

### Validator

The validator:

 * Runs build/test phases
 * Invokes FixLoop on failure
 * Applies fixes
 * Retries
 * Stops only when everything passes

# ▶️ Usage

```
python main.py <work_item_id> --repo <path_to_repo>
```

Example:

```
python main.py 400 --repo D:\git\mav-user-api-sdlc-poc
```

To run only build/test + FixLoop (no GitHub/ADO):

```
ORCH_TEST_ONLY=1 python main.py <id> --repo <path>
```
Create an .env file or use system environment variables to cover the below:

```
ENV=local
GITHUB_TEST_ONLY=0
ORCH_TEST_ONLY=0
ADO_ORG=ABC
ADO_PROJECT=GUID
ADO_PAT=XXXX
GITHUB_TOKEN=XXXX
ANTHROPIC_API_KEY=XXXX
```

# 🧩 Supported Repo Types

## Backend (.NET)

 * Clean Architecture
 * Vertical slices
 * Controllers, Services, Models
 * EF Core
 * CQRS
 * Unit, Integration, Component tests
 * Health checks
 * .NET 8 / .NET 10

## Frontend (React / Next.js)

 * TypeScript
 * ESLint
 * Prettier
 * Next.js App Router
 * React components
 * API routes

# 📁 Project Structure

```
orchestrator/
  main.py
  validator.py
  fix_loop.py
  file_editing.py
  utils/
  architecture/
  mcp-servers/
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
```

# 🔧 Requirements

 * Python 3.10+
 * .NET SDK (for backend repos)
 * Node.js (for frontend repos)
 * GitHub MCP server
 * ADO MCP server
 * Anthropic API key

# 🔒 License

Internal use only.
