# 11. How to Onboard New Repos

_A step‑by‑step guide to making any repo orchestrator‑ready_

The orchestrator is repo‑agnostic. It can onboard:

*   .NET backend repos    
*   React/Next.js frontend repos    
*   Full‑stack repos    
*   Multi‑module repos    
*   Clean Architecture repos
    
This page explains how to onboard a new repo safely.

## 1. Requirements for a New Repo

A repo must have:

### ✔ A build command

*   `.NET`: `dotnet build`    
*   Node: `npm run build`    

### ✔ A test command

*   `.NET`: `dotnet test`    
*   Node: `npm test`    

### ✔ A deterministic folder structure

Backend:

    src/<ModuleName>/
    tests/<ModuleName>.Tests/
    

Frontend:

    src/
    pages/ or app/
    components/
    

### ✔ A GitHub repo

### ✔ ADO Work Items

### ✔ No uncommitted changes

## 2. Onboarding Steps

### Step 1 — Clone the repo locally

    git clone <repo>
    cd <repo>
    

### Step 2 — Run a manual build/test

Backend:

    dotnet build
    dotnet test
    

Frontend:

    npm install
    npm run build
    npm test    

Everything must pass before onboarding.

### Step 3 — Run the orchestrator in test mode

    ORCH_TEST_ONLY=1 python main.py <id> --repo <path>

Verify:

*   Repo copied into `.orchestrator-tmp/`    
*   Build/test run successfully    
*   No FixLoop errors    
*   No architecture violations

### Step 4 — Add repo‑specific conventions (optional)

If the repo has custom rules:

*   Folder naming    
*   DTO conventions    
*   Test folder layout    
*   Module boundaries
    
Add them to:

    architecture/enforcement.py

### Step 5 — Add repo‑specific prompts (optional)

If the repo uses:

*   CQRS    
*   Mediatr    
*   Vertical slices    
*   Custom DI patterns
    
Add them to:

    opencode_prompt_builder.py    

### Step 6 — Run a full orchestrator cycle

Use a small Work Item:

    python main.py 400 --repo <path>    

Verify:

*   Branch created    
*   Commits created    
*   Build/test validated    
*   PR created    
*   PR linked to Work Item    

### Step 7 — Add repo to your “supported repos” list

You can maintain a simple JSON file:

    {
      "repos": [
        {
          "name": "mav-user-api",
          "type": "backend",
          "path": "D:/git/mav-user-api"
        }
      ]
    }    

## 3. Troubleshooting Onboarding

### ❌ Build fails

Fix manually before onboarding.

### ❌ Tests fail

Fix manually before onboarding.

### ❌ FixLoop corrupts files

Ensure `file_editing.py` is updated (no JSON decoding).

### ❌ Architecture violations

Update `enforcement.py`.

### ❌ PR not created

Run in full mode, not ORCH_TEST_ONLY.

## 4. Best Practices

### ✔ Start with a small Work Item

### ✔ Use ORCH_TEST_ONLY first

### ✔ Keep repos clean (no uncommitted changes)

### ✔ Keep architecture rules strict

### ✔ Keep build/test commands deterministic

## 5. Summary

Onboarding a new repo is simple:

1.  Build/test manually    
2.  Run orchestrator in test mode    
3.  Add architecture rules    
4.  Add prompt rules    
5.  Run full mode    
6.  Validate PR    
7.  Add to supported repos
    
Your orchestrator can now support **any number of repos** with consistent, safe automation.

[<< Overview](../../README.md)
 | 
[<< How to Extend the Orchestrator](./11-extend-the-orchestrator.md)
