# 1. Phase 1 — Core Agent Foundations

*   context hierarchy    
*   context shaping    
*   context boundaries    
*   context rehydration    
*   skill registry    
*   skill context profiles    
*   skill routing
    
This is the “architecture spec” for your agentic system.

This phase is **mostly conceptual** because it defines:

*   how agents think    
*   how agents communicate    
*   how agents receive context    
*   how agents avoid context leakage    
*   how skills are structured    
*   how context is shaped and routed
    
These are _design primitives_.

## 1.1 Context Management (most important skill)

Context is the fuel of agentic systems. If you manage it well, the agent behaves like a senior engineer. If you manage it poorly, it hallucinates or breaks things.

### What we need to master now

*   Hierarchical context design
    *   Global context → repo type, architecture rules, model config        
    *   Task context → work item, plan, subtasks        
    *   Local context → file-level, diff-level, test-level
        
*   Context shaping
    *   What to include        
    *   What to exclude        
    *   How to compress        
    *   How to rehydrate on resume
        
*   Context boundaries
    *   What the agent _must_ know        
    *   What the agent _must not_ know        
    *   What the agent _should infer_        
    *   What the agent _should be told explicitly_

### Concrete examples from the orchestrator

*   The`RunState` is a perfect example of _context persistence_.    
*   The `prompt builder` is an example of _context shaping_.    
*   The `architecture enforcer` is an example of _context boundaries_.

## 1.2 Skill Systems (capabilities, tools, behaviours)

Agentic systems are not “one model.” They are **collections of skills**.

We already have:
*   planning
*   decomposition
*   execution
*   fixloop
*   validation
*   architecture enforcement
*   PR enhancement
*   MCP integration
    
Now we need to understand how to _design_ and _manage_ skills.

### What we need to master now

*   Skill boundaries
    *   What a skill should do        
    *   What it should not do        
    *   How skills hand off to each other
        
*   Skill orchestration
    *   Planning → decomposition → execution → validation        
    *   FixLoop → retry → validation → commit
        
*   Skill isolation
    *   Each skill should be independently testable        
    *   Each skill should have its own context
        
*   Skill specialisation
    *   Different models for different skills        
    *   Different prompts for different skills        
    *   Different guardrails for different skills        

### Concrete examples from your orchestrator

*   The decomposition model is a “planning skill.”    
*   The execution model is a “file-edit skill.”    
*   The fixloop model is a “debugging skill.”    
*   The validator is a “test skill.”

## 1.3 Agent Memory (short-term, long-term, working memory)

Memory is the difference between:
*   “AI that reacts”    
*   “AI that reasons”    
*   “AI that works like a team of engineers”
    
You’ve already built:
*   long-term memory → RunState    
*   task memory → TaskMemory    
*   implicit memory → temp workspace    
*   context memory → prompt builder
    
Now we expand it.

### What we need to master now

*   Memory types
    *   short-term (per subtask)        
    *   working memory (per task)        
    *   long-term (per work item)        
    *   persistent memory (across runs)
        
*   Memory shaping
    *   What the agent should remember        
    *   What the agent should forget        
    *   What the agent should summarize        
    *   What the agent should store verbatim
        
*   Memory rehydration
    *   Rebuilding working memory from RunState        
    *   Rebuilding context from the repo        
    *   Rebuilding task memory from logs        

### Concrete examples from your orchestrator

*   RunState → long-term memory    
*   TaskMemory → working memory    
*   prompt builder → short-term memory

## 1.4 Agent Reliability (guardrails, retries, safety)

This is where agentic systems become production-ready.

You already have:
*   strict JSON modes    
*   hardened extractor    
*   hardened sanitizer    
*   retry loops    
*   strict prompts    
*   architecture enforcement    
*   build/test validation    
*   fixloop
    
Now we formalize reliability.

### What we need to master now

*   Guardrail design
    *   JSON-only output        
    *   file-edit-only output        
    *   architecture rules        
    *   test rules        
    *   safety boundaries
        
*   Retry strategies
    *   strict prompt fallback        
    *   model fallback        
    *   skill fallback        
    *   context fallback
        
*   Failure classification
    *   syntax errors        
    *   semantic errors        
    *   architecture violations        
    *   test failures        
    *   build failures
        
*   FixLoop strategies
    *   error extraction        
    *   targeted fixes        
    *   multi-step fixes        
    *   validation loops        

### Concrete examples from your orchestrator

*   Your strict JSON fallback is a guardrail.    
*   Your fixloop is a reliability mechanism.    
*   Your architecture enforcer is a safety boundary.    
*   Your validator is a reliability gate.

[<< Overview](../../README.md)
 | 
[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[Phase 1 — Hierarchical context design >>](./2-phase1-hierarchial-context-design.md)
