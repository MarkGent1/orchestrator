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

## 8.8 Summary

This guide covers:

*   Build failures    
*   Test failures    
*   FixLoop failures    
*   Path issues    
*   DI issues    
*   PR issues
    
Your orchestrator is now stable, but this page helps diagnose edge cases.

[<< Overview](../../README.md)
 | 
[<< Clean Architecture Enforcement Rules](./8-clean-architecture-enforcement.md)
 | 
[Example: Add Basic Health Check Endpoint >>](./10-example-e2e-run.md)
