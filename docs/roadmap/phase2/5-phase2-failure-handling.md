# 2.4 Phase 2 — Failure handling

This is where agentic systems become robust.

Your supervisor must classify failures into categories:

### **Failure Types**

1.  **JSON failure**
    *   executor or fixloop returns malformed JSON        
    *   retry with strict JSON mode
        
2.  **Semantic failure**
    *   JSON is valid but code is wrong        
    *   fixloop agent invoked
        
3.  **Build failure**
    *   validator fails        
    *   fixloop agent invoked
        
4.  **Test failure**
    *   validator fails        
    *   fixloop agent invoked
        
5.  **Architecture violation**
    *   architecture agent reports violation        
    *   fixloop agent invoked
        
6.  **MCP failure**
    *   ADO/GitHub/Azure error        
    *   retry with backoff
        
7.  **Critical failure**
    *   unrecoverable        
    *   supervisor aborts run        

### **Failure Handling Pipeline**

```
    Agent fails
        ↓
    Supervisor classifies failure
        ↓
    If recoverable → FixLoop agent
        ↓
    Re-run failing agent
        ↓
    If still failing → fallback model
        ↓
    If still failing → abort
```    

This is how you build a **self-healing agentic system**.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 2 — Agent interfaces](./4-phase2-agent-interfaces.md)
 | 
[Phase 2 — Logging & observability  >>](./6-phase2-logging-observability.md)
