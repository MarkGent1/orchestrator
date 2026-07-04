# 8. Troubleshooting

This page covers common issues and how to resolve them.

## 8.1 Build Fails Immediately

### Cause

FixLoop corrupted a file (old version).

### Fix

Ensure `file_editing.py` does **not** use `json.loads`.

## 8.2 FixLoop Makes Things Worse

### Cause

FixLoop lacked context or safety rules.

### Fix

Ensure:

*   Clean Architecture enforcement is active    
*   Safety rules are in FixLoop prompt    
*   Path validation is enabled    

## 8.3 PR Not Created

### Cause

Validation failed and FixLoop exhausted attempts.

### Fix

Check:

*   Build output    
*   Test output    
*   FixLoop logs    

## 8.4 Integration Tests Fail

### Cause

Missing DI registrations (common in .NET).

### Fix

Add required services:

    services.AddHealthChecks();
    services.AddScoped<IHealthCheckService, HealthCheckService>();

## 8.5 File Paths Incorrect

### Cause

Missing `workspace_root` in `normalize_path_casing`.

### Fix

Ensure:

    normalize_path_casing(path, repo_type, workspace_root=temp_workspace)

## 8.6 FixLoop Crashes with KeyError

### Cause

FixLoop returned `"file"` but validator expected `"path"`.

### Fix

Use unified path resolution:

    file_path = fix.get("file") or fix.get("path") ...

## 8.7 JSONDecodeError in FixLoop

### Cause

Old version of file writer attempted to JSON‑decode content.

### Fix

Remove all JSON decoding from `file_editing.py`.

## 8.9 Run Crashed Partway Through

### Cause

A bad model response, a build that exhausted FixLoop's retry budget, an MCP timeout, or the model proposing an illegal file path (see 8.10 below) all used to mean the whole run was lost.

### Fix

Just re-run the exact same command:

    python main.py <work_item_id> --repo <path_to_repo>

The orchestrator persists progress to `.orchestrator-state/` as it goes and automatically resumes from the first unfinished subtask — no re-planning, no duplicate branches, no lost commits. See [Resume From a Crash](./14-resume-from-crash.md) for details, including how to discard progress and start over.

## 8.10 "Illegal raw path from model" / Model Invents a New Test Project

### Cause

The model was asked to add tests and, unable to see that an existing test project already existed under `tests/`, invented a brand-new one under `src/` (e.g. `src/Something.Tests/...`). Clean Architecture enforcement correctly rejects this as a new module.

### Fix

This is fixed at the source: the repo tree shown to the model now includes `tests/` paths (see [Clean Architecture Enforcement Rules § 7.7.1](./8-clean-architecture-enforcement.md)) and the prompt includes explicit test-placement rules.

If it happens anyway (or for any other illegal-path edit from the model), it's no longer fatal: `task_executor.py` catches the error, logs it clearly, and treats that one subtask as if it produced no changes — the run continues and resume will retry just that subtask later if needed.

**Known gap:** this containment currently only covers the main task-execution path. An illegal path proposed *during a FixLoop retry* (i.e. while fixing a build/test failure) can still crash the run the same way this used to.

## 8.11 Summary

This guide covers:

*   Build failures    
*   Test failures    
*   FixLoop failures    
*   Path issues    
*   DI issues    
*   PR issues
*   Crashed/interrupted runs
    
Your orchestrator is now stable, but this page helps diagnose edge cases.

[<< Overview](../../README.md)
 | 
[<< Clean Architecture Enforcement Rules](./8-clean-architecture-enforcement.md)
 | 
[Example: Add Basic Health Check Endpoint >>](./10-example-e2e-run.md)
