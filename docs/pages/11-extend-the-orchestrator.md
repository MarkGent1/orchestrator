# 10. How to Extend the Orchestrator

The orchestrator is intentionally designed to be **modular**, **composable**, and **safe to extend**. Every major capability lives in its own module, with clear boundaries and single‑responsibility files.

This page explains **how to add new features** without breaking the existing SDLC engine.

## 1. Extension Philosophy

The orchestrator follows three principles:

### 1.1. Isolation

Every capability lives in its own file or module:

*   Build logic → `backend_build.py`, `frontend_build.py`    
*   Fix logic → `fix_loop.py`    
*   Git logic → `git_workflow.py`    
*   PR logic → `pr_enhancer.py`    
*   Architecture rules → `architecture/enforcement.py`
    
This makes extensions safe and predictable.

### 1.2. Temp‑Workspace Execution

All changes happen inside:

    <repo>/.orchestrator-tmp/    

This means:

*   You can experiment freely    
*   FixLoop cannot corrupt your real repo    
*   New features cannot break your working tree    

### 1.3. Declarative Pipelines

Validation phases are declared as:

    ("build", run_backend_build)
    ("test", run_backend_tests)    

To add a new phase, you simply add a new tuple.

## 2. Extending the Orchestrator

Below are the **five most common extension scenarios**.

### 2.1 Add a New Validation Phase

_(e.g., Security Scan, SAST, Dependency Audit)_

### Step 1 — Create a new file

Example: `backend_security_scan.py`

    def run_backend_security_scan(repo_path: Path):
        # run your scanner here
        ok = ...
        output = ...
        return ok, output    

### Step 2 — Add it to the backend pipeline

In `validator.py`:

    phases = [
        ("build", run_backend_build),
        ("test", run_backend_tests),
        ("security", run_backend_security_scan),
    ]    

### Step 3 — FixLoop automatically supports it

No changes needed — FixLoop will:

*   capture errors    
*   generate fixes    
*   retry    

## 2.2 Add a New Repo Type

_(e.g., Python, Go, Java, Terraform)_

### Step 1 — Add a new repo detector

In `repo_type.py`:

    if (repo_root / "pyproject.toml").exists():
        return "python"    

### Step 2 — Add new validation files

Example:

    python_build.py
    python_test.py
    python_lint.py    

### Step 3 — Add phases to validator

In `validator.py`:

    elif self.repo_type == "python":
        phases = [
            ("build", run_python_build),
            ("test", run_python_tests),
            ("lint", run_python_lint),
        ]    

### Step 4 — Add language rules to FixLoop

In `fix_loop.py`:

    elif self.repo_type == "python":
        language_rules = """
        This is a Python repository.
        You MUST generate only .py files.
        You MUST NOT generate C#, TS, JS, etc.
        """
Done.

## 2.3 Add a New MCP Server

_(e.g., Azure, AWS, Jira, Slack, PagerDuty)_

### Step 1 — Create a new client

Example: `azure_mcp_client.py`

### Step 2 — Add public methods

(e.g., `deployToTest`, `getLogs`, `restartService`)

### Step 3 — Call it from `main.py` or a new module

Example:

    azure = AzureMcpClient(...)
    await azure.deploy_to_test(...)    

### Step 4 — Add new SDLC phases

Example: Deployment phase after validation:

    await azure.deploy_to_test(branch)
    await azure.run_smoke_tests()    

## 2.4 Add New Architecture Rules

_(e.g., new folder types, new naming conventions)_

### Step 1 — Update `architecture/enforcement.py`

Add new allowed folders:

    ALLOWED_FOLDERS = [
        "Controllers",
        "Models",
        "DTOs",
        "Services",
        "Interfaces",
        "Setup",
        "Extensions",
        "Queries",       # new
        "Commands",      # new
    ]    

Add new naming rules:

    if folder == "Queries" and not file.endswith("Query.cs"):
        return False    

### Step 2 — FixLoop automatically enforces them

No changes needed.

## 2.5 Add New PR Enhancements

_(e.g., diagrams, architecture summaries, test coverage)_

### Step 1 — Update `pr_enhancer.py`

Add new sections:

    def add_architecture_summary(self, pr_body, repo_context):
        pr_body += "### Architecture Impact\n"
        pr_body += repo_context.describe_changes()
        return pr_body    

### Step 2 — Call it in `create_pr_description()`

## 3. Extending FixLoop

FixLoop is intentionally modular.
You can extend it in three ways:

### 3.1 Add More Safety Rules

In `fix_loop.py`:

    ### SAFETY RULES
    - DO NOT modify Program.cs unless error mentions it
    - DO NOT modify .csproj unless error mentions missing packages
    - DO NOT create new folders outside allowed module structure

### 3.2 Add File‑Context to Prompts

_(Highly recommended for complex repos)_
Add:

    file_context = self._collect_file_context(error_output)    

Then include it in the prompt.

### 3.3 Add Diff‑Sanity Checks

Reject edits that:

*   modify too many files    
*   touch unrelated modules    
*   rewrite Program.cs    
*   rewrite csproj    

## 4. Extending Task Execution

You can extend Module 4 by:

### 4.1 Adding New Sub‑Task Types

Example: “Generate API docs”
Add to `task_decomposer.py`:

    "Generate API documentation"    

### 4.2 Adding Multi‑Pass Refinement Rules

Example: run a second pass for missing imports.
In `task_executor.py`:

    for pass_num in range(1, max_passes+1):
        run_pass(pass_num)    

### 4.3 Adding Task Memory

Store new metadata:

    memory["changed_files"].append(file)
    memory["errors"].append(error_output)    

## 5. Extending Deployment (Future Module)

Once Azure MCP is added, you can extend:

*   Deploy to TEST    
*   Run smoke tests    
*   Fetch logs    
*   Tear down environments    
*   Update Work Item with deployment results
    
This becomes Module 5.

## 6. Best Practices for Extensions

### ✔ Keep modules isolated

Never mix build logic with FixLoop logic.

### ✔ Keep prompts declarative

Avoid procedural instructions.

### ✔ Keep FixLoop minimal

Fix only what the error demands.

### ✔ Keep architecture rules strict

This prevents hallucinated folders.

### ✔ Keep temp‑workspace model

Never modify the real repo directly.

## 7. Summary

This page gives you a complete blueprint for extending the orchestrator safely:

*   Add new repo types    
*   Add new validation phases    
*   Add new MCP servers    
*   Add new architecture rules    
*   Add new PR enhancements    
*   Add new SDLC phases    
*   Add new FixLoop capabilities
    
Your orchestrator is now a **platform**, not a script — and this page shows how to grow it cleanly.

[<< Overview](../../README.md)
 | 
[<< Example: Add Basic Health Check Endpoint](./10-example-e2e-run.md)
 | 
[How to Onboard New Repos >>](./12-onboard-new-repos.md)
