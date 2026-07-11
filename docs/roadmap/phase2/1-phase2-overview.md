# 2. Phase 2 — From Skills to Agents

The Orchestrator (Phase 0) already has:

*   **Planner** → planning agent    
*   **Decomposer** → decomposition agent    
*   **Executor** → code‑editing agent    
*   **FixLoop** → debugging agent    
*   **Validator** → verification agent    
*   **ArchitectureEnforcer** → architecture agent    
*   **PR Enhancer** → summarisation agent    
*   **RunState / TaskMemory** → memory agents    
*   **ADO / GitHub / Azure MCP** → integration agents
    
Phase 2 is about treating each of these as **agents**:

*   with their own context profile    
*   with their own memory scope    
*   with their own lifecycle    
*   with their own logs/metrics    
*   with explicit coordination rules

## 2.1 Core agent patterns to introduce

We’ll be working with these patterns:

*   **Plan‑and‑Execute** Planner → Decomposer → Executor → Validator → PR    
*   **Supervisor–Worker** A supervisor agent monitors progress, decides which agent runs next, and reacts to failures.    
*   **Reflective agents** Agents that can look at their own output and refine it (e.g. FixLoop, PR Enhancer).    
*   **Tool‑augmented agents** Agents that call MCP servers (ADO, GitHub, Azure) as tools.    
*   **Memory‑augmented agents** Agents that read/write RunState and TaskMemory deliberately.    

## 2.2 Agent roles in your system

A clean Phase 2 mapping for you:

*   **Supervisor agent**
    *   Orchestrates the whole run.        
    *   Decides when to plan, decompose, execute, fix, validate, and push.
        
*   **Planning agent**
    *   Owns work item → plan.
        
*   **Decomposition agent**
    *   Owns task → subtasks.
        
*   **Execution agent**
    *   Owns subtask → file edits.
        
*   **Debug agent (FixLoop)**
    *   Owns error → corrected edits.
        
*   **Validation agent**
    *   Owns build/test/architecture checks.
        
*   **Architecture agent**
    *   Owns module rules and violations.
        
*   **PR agent**
    *   Owns PR body and narrative.
        
*   **Memory agent**
    *   Owns RunState and TaskMemory.
        
*   **Integration agents**
    *   Own ADO, GitHub, Azure operations.
        
The current orchestrator already behaves like this.

Phase 2 is about **making those roles explicit**.

## 2.3 What changes architecturally

Instead of `main.py` being the “god function”, Phase 2 moves toward:

*   a **Supervisor** that:
    *   reads RunState        
    *   inspects current progress        
    *   chooses the next agent to invoke        
    *   passes the right context packet        
    *   reacts to failures (e.g. call FixLoop, or bail out)
        
*   agents that:
    *   declare their required context        
    *   declare their outputs        
    *   declare their failure modes        
    *   log their decisions
        
You don’t have to rewrite everything. This can start as a thin layer over your existing functions.

## 2.4 How we can tackle Phase 2

We can break Phase 2 into:

1.  **Agent role definitions** Formalise each agent’s responsibilities and boundaries.    
2.  **Supervisor design** A small orchestrator that decides which agent runs next based on RunState.    
3.  **Agent interfaces** Standardise how agents receive context and return results.    
4.  **Failure handling** Define how the supervisor reacts to build failures, JSON failures, MCP failures, etc.    
5.  **Logging & observability** Per‑agent logs, timelines, and metrics.

[<< Overview](../../README.md)
 | 
[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[Agent role definitions >>](./2-phase2-agent-roles.md)
