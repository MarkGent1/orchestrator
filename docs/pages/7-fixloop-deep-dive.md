# 6. FixLoop Deep Dive

FixLoop is the orchestrator’s **self‑healing engine**. It automatically fixes build/test/lint/format failures using AI‑generated patches.

## 6.1 Purpose

FixLoop ensures:

*   No broken PRs    
*   No corrupted files    
*   No hallucinated folders    
*   No invalid architecture    
*   No unvalidated code reaches GitHub    

## 6.2 FixLoop Flow

    1. Phase fails (build/test/lint/format)
    2. Validator captures error output
    3. FixLoop builds a repair prompt
    4. OpenCode returns JSON file edits
    5. Edits validated by Clean Architecture rules
    6. Edits applied safely in temp workspace
    7. Phase re‑runs
    8. Repeat until fixed or attempts exhausted
    
## 6.3 Prompt Structure

FixLoop prompt includes:

*   Error output    
*   Repo type    
*   Clean Architecture rules    
*   Module structure    
*   Safety rules    
*   JSON‑only output contract    

## 6.4 Safety Rules

FixLoop is forbidden from:

*   Creating new modules    
*   Moving files across modules    
*   Rewriting Program.cs unless error demands it    
*   Editing csproj unless error demands it    
*   Adding random NuGet packages    
*   Inventing new folders    
*   Overwriting unrelated files    

## 6.5 Path Validation

Every edit is validated:

*   Must be inside an existing module    
*   Must follow naming conventions    
*   Must follow folder rules    
*   Must not escape repo root    

## 6.6 File Editing Safety

`file_editing.py` ensures:

*   No JSON decoding    
*   No escape corruption    
*   No stray backslashes    
*   No invalid characters    
*   No overwriting outside module    

## 6.7 Example FixLoop Cycle

    === BUILD OUTPUT ===
    CS0104: ambiguous reference
    
    === Fix attempt 1 ===
    Applied 1 file edit
    
    === BUILD OUTPUT (after fix) ===
    Build succeeded
    
## 6.8 Summary

FixLoop is now:

*   Deterministic    
*   Safe    
*   Architecture‑aware    
*   Minimal‑diff    
*   Non‑destructive    
*   Fully integrated

[<< Overview](../../README.md)
 | 
[<< Architecture Overview](./6-architecture-overview.md)
 | 
[Clean Architecture Enforcement Rules >>](./8-clean-architecture-enforcement.md)
