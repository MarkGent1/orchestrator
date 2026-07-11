# 1.1.3 Phase 1 — Context Compression

**Goal:** shrink context without losing meaning.

Compression is not “summarisation.”

Compression is **semantic distillation**: removing everything that doesn’t change the agent’s decision.

Think of it like engineering signal‑to‑noise ratio.

# The Four Compression Targets

Every agentic system compresses four types of context:

### 1. Work Item / Task Context

Large → narrative, human-written, often noisy
Compressed → structured, actionable, minimal

### 2. File / Code Context

Large → entire file, entire module
Compressed → relevant region + structural anchors

### 3. Error / Log Context

Large → full build logs, full test output
Compressed → actionable error slice + minimal reproduction context

### 4. Architecture / Rule Context

Large → full rule set
Compressed → rule relevant to the file/subtask

# Compressing Work Item & Task Context

This is the first place engineers overfeed models.

Your planner and decomposer should never see:
*   full work item description    
*   full acceptance criteria    
*   full repo    
*   full code    
*   full tests
    
They need only the semantic core.

### ✔ Compression pattern: Task Distillation

Take this:

```
    Add UsersController returning a stub list of users.
    This should include:
    - IUserService
    - UserService
    - GET /users
    - DI registration
    - Unit tests
```    

Distill to:

```
    Goal: Add UsersController with stub user list.
    Required components:
    - IUserService
    - UserService
    - GET /users endpoint
    - DI registration
    - Unit tests
```   

This is **lossless compression**:
 - no meaning lost
 - no noise retained

### ✔ Implementation in your orchestrator

Your decomposition model already receives a compressed version.

We can formalise this into a **Task Context Compressor** module later.

# Compressing File / Code Context

This is the most important compression skill for execution agents.

### ❌ Never send the whole file

Even Sonnet will hallucinate if you give it:
*   500 lines    
*   multiple classes    
*   unrelated methods    
*   unrelated imports    
*   unrelated attributes    

### ✔ Instead: slice the file into a “Relevant Region Packet”

A Relevant Region Packet contains:
1.  The exact region to edit    
2.  The surrounding structural anchors    
3.  The file header (namespace, usings)    
4.  The class signature    
5.  The method signature    
6.  The architecture rule relevant to this file
    
Example:

```
    File: UserService.cs
    Relevant region: GetUsers()
    Anchor above: class UserService : IUserService
    Anchor below: end of method
    Architecture rule: Services must not reference Controllers
```

This is the **minimum viable context** for a file-edit agent.

### ✔ Implementation in your orchestrator

Your prompt builder already slices files.

We can enhance it with:
*   anchor detection    
*   region extraction    
*   architecture rule injection    
*   semantic slicing    

# Compressing Error / Log Context

Build/test logs are huge. FixLoop models choke on them unless you compress.

### ❌ Never send full logs

They contain:
*   noise    
*   timestamps    
*   unrelated warnings    
*   unrelated test failures    
*   stack traces from other modules    

### ✔ Instead: extract the “Actionable Error Slice”

This contains:
1.  The failing file    
2.  The failing line    
3.  The failing test    
4.  The assertion message    
5.  The minimal reproduction context
    
Example:

```
    Error: NullReferenceException in UsersController.cs: line 22
    Cause: _userService is null
    Fix: DI registration missing
```

This is the semantic core of the error.

### ✔ Implementation in your orchestrator

Your BuildTestValidator already extracts error slices.

We can formalise this into an **Error Context Compressor**.

# Compressing Architecture / Rule Context

Architecture rules are global, but execution agents only need the **rule relevant to the file**.

### ❌ Never send the full rule set

It’s noise.

### ✔ Instead: send the “Relevant Rule Packet”

Example:

```
    Rule: Controllers must not depend on Services directly.
``` 

Or:

```
    Rule: Services must not reference Controllers.
``` 

Or:

```
    Rule: Models must be pure DTOs.
``` 

This is the **local architecture constraint**.

### ✔ Implementation in your orchestrator

Your CleanArchitectureEnforcer already knows the rule set.

We can add a **Rule Context Router** to extract the relevant rule.

# Compression Techniques (the actual engineering patterns)

Here are the compression techniques you’ll use across all skills:

### 1. Semantic Distillation

Remove words that don’t change meaning.

### 2. Structural Slicing

Extract only the relevant region of a file.

### 3. Anchor Extraction

Include structural anchors so the model knows where it is.

### 4. Error Slicing

Extract only the actionable part of logs.

### 5. Rule Routing

Send only the architecture rule relevant to the file.

### 6. Context Profiles

Each skill gets a different compressed context.

### 7. Context Boundaries

Prevent leakage (planner must not see code, executor must not see plan).

### 8. Context Rehydration

On resume, rebuild compressed context from RunState + workspace.

# The Context Compression Pipeline (your future module)

Here’s the pipeline we’ll build:

```
    Raw Context
        ↓
    Context Classifier (task/file/error/rule)
        ↓
    Context Slicer (region extraction)
        ↓
    Context Distiller (semantic compression)
        ↓
    Context Router (skill-specific shaping)
        ↓
    Context Packet (final shaped context)
```    

This is how you build **lossless**, **minimal**, **actionable context packets**.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 1 — Context shaping](./3-phase1-context-shaping.md)
 | 
[Phase 1 — Context rehydration >>](./5-phase1-context-rehydration.md)
