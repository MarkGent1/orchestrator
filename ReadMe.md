# Table of Contents

1. [Overview](README.md)
2. [Advancing the Orchestrator](docs/pages/1-advancing-the-orchestrator.md)
3. [Module 1: Work Item + Plan + Tasks](docs/pages/2-module-1.md)
4. [Module 2: Branch + PR Automation](docs/pages/3-module-2.md)
5. [Module 3: Build, Test, Lint, Format & Auto‑Fix Validation](docs/pages/4-module-3.md)
6. [Module 4: Multi‑Task, Multi‑Phase, Multi‑Commit SDLC Loop](docs/pages/5-module-4.md)
7. [Architecture Overview](docs/pages/6-architecture-overview.md)
8. [FixLoop Deep Dive](docs/pages/7-fixloop-deep-dive.md)
9. [Clean Architecture Enforcement Rules](docs/pages/8-clean-architecture-enforcement.md)
10. [Troubleshooting](docs/pages/9-troubleshooting.md)
11. [Example: Add Basic Health Check Endpoint](docs/pages/10-example-e2e-run.md)
12. [How to Extend the Orchestrator](docs/pages/11-extend-the-orchestrator.md)
13. [How to Onboard New Repos](docs/pages/12-onboard-new-repos.md)
14. [Model Capabilities](docs/pages/13-model-capabilities.md)
15. [Resume From a Crash](docs/pages/14-resume-from-crash.md)
16. [Roadmap for advancing AI Engineering Practices](docs/roadmap/1-roadmap-overview.md)

# Overview

# 🚀 Orchestrator — Autonomous Multi‑Model SDLC Engine

**AI‑driven Work Item → Branch → Code → Build/Test → Fix → PR automation**

The orchestrator performs a **full end‑to‑end SDLC loop** using:

- Azure DevOps Work Items  
- GitHub repositories  
- Multi‑model AI agents (Claude + OpenAI)  
- Clean Architecture enforcement  
- Automated build/test validation  
- Self‑healing FixLoop  
- Automated PR creation + linking  

All work happens inside a **temporary workspace**, keeping your real repo clean until the PR is created.

---

# ✨ Multi‑Model AI Architecture

The orchestrator uses **four specialised AI agents**, each powered by a different model:

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

This makes the orchestrator a **true multi‑agent SDLC engine**.

---

# 🧠 Core Capabilities

## 1. Work Item Planning (Claude Sonnet)

- Reads ADO Work Item  
- Extracts title, description, acceptance criteria  
- Generates a structured task plan  
- Validates Work Item quality  
- Adds comments back to ADO  
- Idempotent: if the Work Item already has child tasks (e.g. from a previous run), reuses that plan instead of generating and creating a duplicate one

## 2. Task Decomposition (GPT‑5.4‑mini)

- Breaks tasks into 2–6 subtasks  
- Produces clean JSON arrays  
- Cheap + fast  

## 3. Task Execution (Claude Haiku)

- Creates feature branch  
- Executes subtasks  
- Generates code edits  
- Applies edits inside temp workspace  
- Commits changes per subtask  
- Pushes branch  
- Opens PR  
- Enhances PR description  

## 4. Build/Test Validation + FixLoop (Claude Haiku)

- Runs backend or frontend build  
- Runs unit/integration/component tests  
- Runs lint/format (frontend)  
- If anything fails → FixLoop kicks in  
- FixLoop generates minimal, safe file edits  
- Edits validated by Clean Architecture rules  
- Build/test reruns  
- Loop continues until green or attempts exhausted  

---

# 🧩 Clean Architecture Enforcement (Backend)

Strict backend rules ensure AI cannot hallucinate architecture:

- Only modifies files inside existing modules  
- Allowed folders: Controllers, Models, DTOs, Services, Interfaces, Setup, Extensions  
- No new modules  
- No moving files across modules  
- No rewriting architecture  
- Strict naming conventions enforced  

---

# 🛠️ How It Works Internally

## Temporary Workspace

The orchestrator copies your repo into:

```
<repo>/.orchestrator-tmp/
```

All code generation, builds, tests, and fixes happen **inside the temp workspace**.

Your real repo is untouched until the PR is created.

---

## Resume From a Crash

Every run persists its progress — branch name, task plan, subtask breakdown, per-subtask completion, validation status, and PR URL — to:

```
<orchestrator-dir>/.orchestrator-state/<repo-key>-<work_item_id>.json
```

If a run crashes partway through (bad model output, a build that exhausts FixLoop's retry budget, an MCP timeout, etc.), just **re-run the exact same command**. The orchestrator detects the existing state, checks out the same feature branch, and picks up from the first unfinished subtask — skipping re-planning, branch creation, and every task/subtask already completed and committed. Once a run fully completes (PR opened and linked), its state file is deleted.

See [Resume From a Crash](docs/pages/14-resume-from-crash.md) for the full details, including how to discard progress and start a Work Item over from scratch.

---

## Multi‑Agent AI Flow

```
ADO Work Item
↓
Claude Sonnet → Planning
↓
GPT‑5.4‑mini → Decomposition
↓
Claude Haiku → Task Execution
↓
Build/Test
↓
If fail → Claude Haiku FixLoop
↓
Push Branch
↓
Open PR
↓
Link PR to Work Item
```

---

## FixLoop (Self‑Healing Engine)

FixLoop:

- Reads build/test errors  
- Generates minimal file edits  
- Validates paths with Clean Architecture rules  
- Applies edits  
- Rebuilds + retests  
- Repeats until fixed  

FixLoop now includes:

- Dynamic model selection  
- Safe path resolution  
- No JSON corruption  
- No destructive overwrites  
- No csproj edits unless required  
- Minimal diff philosophy  

---

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

Environment variables:

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
OPENAI_API_KEY=XXXX
```

# 🧩 Supported Repo Types

Repos are expected to be **single-type**, with `src/` and `tests/` directly at the repository root. There is no support for a nested `frontend/`/`backend/` subfolder convention, and no monorepo support — repo type is detected purely from what exists at the root:

 * **Backend** — a `.sln`/`.slnx` at the root, or a `.csproj` anywhere under the repo
 * **Frontend** — a `package.json` at the root
 * **Fullstack** — both signals present at once (runs both validation pipelines)
 * **Unknown** — neither signal found (pre-flight fails with a clear message)

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
  opencode_client/
  openai_client/
  utils/
  architecture/
  mcp_servers/
  tests/

  main.py
  validator.py
  fix_loop.py
  file_editing.py
  model_selector.py
  model_constants.py
  run_state.py
  repo_type.py
  preflight_validator.py
  prompt_builder.py
  git_workflow.py
  backend_build.py
  backend_test.py
  frontend_build.py
  frontend_test.py
  frontend_lint.py
  frontend_format.py
  task_decomposer.py
  task_executor.py
  task_memory.py
  work_item_planning.py
  pr_enhancer.py

  pytest.ini
  requirements-dev.txt
```

`.orchestrator-tmp/` (inside the target repo) and `.orchestrator-state/` (inside `orchestrator/`) are both created at runtime and are not part of the checked-in project structure.

# 🧪 Testing the Orchestrator Itself

The orchestrator has its own pytest suite under `tests/`, covering the JSON extraction/sanitization pipeline, path casing normalization, repo-type detection, Clean Architecture enforcement, the MCP clients, the resume/state persistence, and a full crash-then-resume end-to-end scenario. Everything is mocked (no real LLM/ADO/GitHub/dotnet/npm calls), so it runs in a couple of seconds:

```
pip install -r requirements-dev.txt
pytest
```

Run this before merging any change to the orchestrator itself.

# 🔧 Requirements

 * Python 3.10+ (some modules use `pathlib.Path.walk()`, which requires Python 3.12+ — the project's own `.venv` should target 3.12 or newer)
 * .NET SDK (for backend repos)
 * Node.js (for frontend repos)
 * GitHub MCP server
 * ADO MCP server
 * Anthropic API key
 * OpenAI API key

# 🔒 License

Internal use only.

[Advancing the Orchestrator >>](./docs/pages/1-advancing-the-orchestrator.md)
