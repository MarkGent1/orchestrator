# 2.3 Phase 2 — Agent interfaces

Every agent must implement a standard interface.

This is the key to making your system modular and extensible.

### The Agent Interface (conceptual)

```
Agent.run(context_packet) -> AgentResult
```  

Where:

### **Context Packet**

Contains only the context allowed for that agent:

*   shaped    
*   sliced    
*   compressed    
*   boundary‑checked    
*   rehydrated    

### **AgentResult**

Contains:

*   success/failure    
*   output payload    
*   error (if any)    
*   metadata (latency, retries, cost)    

### **Agent Metadata**

Each agent declares:

*   required context layers    
*   forbidden context layers
*   model profile    
*   reliability strategy    
*   dependencies    
*   output contract
    
This is the foundation for multi-agent orchestration.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 2 — Supervisor design](./3-phase2-supervisor-design.md)
 | 
[Phase 2 — Failure handling  >>](./5-phase2-failure-handling.md)
