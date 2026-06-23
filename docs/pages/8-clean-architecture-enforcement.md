# 7. Clean Architecture Enforcement Rules

The orchestrator enforces strict Clean Architecture boundaries for backend repos.

## 7.1 Module Detection

A module is any folder under:

    src/<ModuleName>/
    
that contains a `.csproj`.

## 7.2 Allowed Folders Inside a Module

    Controllers/
    Models/
    DTOs/
    Services/
    Interfaces/
    Setup/
    Extensions/

No other folders are allowed.

## 7.3 Forbidden Actions

FixLoop and Task Execution may **not**:

*   Create new modules    
*   Move files between modules    
*   Create new top‑level folders under `src/`    
*   Modify `.csproj` unless error demands it    
*   Rewrite Program.cs unless error demands it    
*   Invent new architecture    

## 7.4 Naming Conventions

*   Folders → PascalCase    
*   Files → PascalCase    
*   Interfaces → start with `I`    
*   DTOs → end with `Dto`    
*   Controllers → end with `Controller`    
*   Services → end with `Service`    

## 7.5 Path Validation

Every file edit must:

*   Stay inside the module    
*   Match existing casing    
*   Match existing folder structure    
*   Not escape repo root    

## 7.6 Example Valid Paths

    src/UserMgmt/Controllers/UserController.cs
    src/UserMgmt/Services/UserService.cs
    src/UserMgmt/Models/User.cs

## 7.7 Example Invalid Paths

    src/Controllers/UserController.cs
    src/UserMgmt/NewFolder/Whatever.cs
    src/NewModule/...

## 7.8 Summary

Clean Architecture enforcement ensures:

*   No hallucinated architecture    
*   No broken module boundaries    
*   No invalid folder structures    
*   No destructive edits

[<< Overview](../../README.md)
 | 
[<< FixLoop Deep Dive](./7-fixloop-deep-dive.md)
 | 
[Troubleshooting >>](./9-troubleshooting.md)
