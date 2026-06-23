# 3. Module 3: Build, Test, Lint, Format & Auto‑Fix Validation

# 3.1 Overview

Module 3 is the orchestrator’s **quality gate**. It transforms the system from “AI that writes code” into a **safe, production‑ready AI engineer**.

Every branch produced by the orchestrator is guaranteed to:
*   **Build successfully**    
*   **Pass all tests**    
*   **Lint cleanly (frontend)**    
*   **Format cleanly (frontend)**    
*   **Auto‑fix errors before PR creation**
    
This module runs **after Module 2** finishes generating and committing all code changes.

# 3.2. Purpose of Module 3

Module 3 ensures:
*   No broken builds    
*   No failing tests    
*   No lint/format violations    
*   No corrupted files    
*   No invalid folder structures    
*   No PR is created unless the branch is **fully validated**
    
If validation fails and cannot be fixed → **no PR is created**.

This protects your main branch and your reviewers.

# 3.3. High‑Level Flow

After Module 2 finishes applying all task edits:

    Task Loop → Commit → BuildTestValidator → Push → PR → Link to Work Item
    
Module 3 sits between:

*   Task Loop (Module 2)
*   Push Branch
    
It ensures the branch is safe to merge.

# 3.4. Repo‑Type Aware Validation

The orchestrator automatically detects repo type:

    Backend  → .NET (.sln present)
    Frontend → Node/React/Next.js (package.json present)

Each repo type has its own validation pipeline.

# 3.5. Validation Pipelines

## 3.5.1 Backend (.NET)

Code

    dotnet build
    dotnet test
    (auto‑fix if needed)    

## 3.5.2 Frontend (React / Next.js / Node)

Code

    npm install
    npm run build
    npm run test
    npm run lint
    npm run format
    (auto‑fix if needed)    

Each phase is atomic and can trigger FixLoop.

# 3.6. File Structure (Flat, Clean)

```
validator.py
fix_loop.py
file_editing.py

# Backend
backend_build.py
backend_test.py

# Frontend
frontend_build.py
frontend_test.py
frontend_lint.py
frontend_format.py
```
    
Each file has a **single responsibility**.

# 3.7. BuildTestValidator

`validator.py` orchestrates the entire Module 3 pipeline.

### Responsibilities

*   Detect repo type    
*   Run build/test/lint/format phases    
*   Trigger FixLoop on failure    
*   Re‑run failing phases    
*   Stop after `max_fix_attempts`    
*   Return success/failure to `main.py`    

### Backend phases

    build → test
    
### Frontend phases

    build → test → lint → format

# 3.8. Auto‑Fix Loop (FixLoop)

When a phase fails:
1.  Capture error output    
2.  Build a FixLoop prompt    
3.  Send to OpenCode    
4.  Receive JSON file edits    
5.  Validate edits with Clean Architecture rules    
6.  Apply edits safely    
7.  Re‑run the failing phase    
8.  Repeat until fixed or attempts exhausted
    
If all attempts fail → **no PR is created**.

# 3.9. FixLoop Prompt (Smart, Repo‑Aware)

FixLoop instructs OpenCode to:
*   Fix .NET build errors    
*   Fix .NET test failures    
*   Fix missing namespaces    
*   Fix ambiguous references    
*   Fix incorrect file placement    
*   Fix TypeScript errors    
*   Fix missing imports    
*   Fix ESLint violations    
*   Fix Prettier formatting
    
And always return **strict JSON**.

FixLoop now includes:
*   Clean Architecture enforcement    
*   Safe path validation    
*   No JSON corruption    
*   No destructive overwrites    
*   No csproj edits unless required    
*   No Program.cs rewrites unless error demands it

# 3.10. Integration with main.py

Module 3 is triggered here:

    validator = BuildTestValidator(repo_path=repo_path, temp_workspace=temp, max_fix_attempts=3)
    ok, message = await validator.run_validation()
    
    if not ok:
        print(f"Build and test validation failed: {message}")
        return    

Only after validation succeeds does the orchestrator:
*   Push the branch    
*   Open the PR    
*   Link the PR to the Work Item
    
This is your **merge gate**.

# 3.11. Benefits of Module 3

### ✔ Zero broken PRs

Every PR builds, tests, lints, and formats cleanly.

### ✔ Automatic fixes

FixLoop repairs errors before you ever see them.

### ✔ Full‑stack support

Backend and frontend repos validated with equal rigor.

### ✔ Repo‑agnostic

Works for .NET, React, Next.js, Node, and mixed repos.

### ✔ Safe automation

No PR is created unless the branch is production‑ready.

# 3.12. Example Output

    === BUILD OUTPUT ===
    Build FAILED: missing namespace
    
    === Fix attempt 1 for build errors ===
    Applied 2 file edits
    
    === BUILD OUTPUT (after fix) ===
    Build succeeded
    
    === TEST OUTPUT ===
    All tests passed

Frontend example:

    === LINT OUTPUT ===
    3 ESLint errors
    
    === Fix attempt 1 for lint errors ===
    Applied 1 file edit
    
    === LINT OUTPUT (after fix) ===
    No issues found

# 3.13. Summary

Module 3 is the orchestrator’s **quality assurance engine**.

It ensures:
*   Every branch is valid    
*   Every PR is safe    
*   Every repo type is supported    
*   Every error is auto‑fixable    
*   Every change is validated before merge
    
This is the foundation for a **fully autonomous SDLC loop**.

[<< Overview](../../README.md)
 | 
[<< Module 2: Branch + PR Automation](./3-module-2.md)
 | 
[Module 4: Multi‑Task, Multi‑Phase, Multi‑Commit SDLC Loop >>](./5-module-4.md)
