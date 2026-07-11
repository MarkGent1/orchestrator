# 2.1 Phase 2 — Agent role definitions

Each agent must have a **clear, atomic responsibility**.

This prevents overlap, confusion, and context leakage.

Here are the formal roles for your system:

### 🧠 **Planning Agent**

*   Converts Work Item → Plan    
*   High‑level reasoning    
*   No code access    
*   Produces structured tasks    

### 🧩 **Decomposition Agent**

*   Converts Task → Subtasks    
*   Architectural awareness    
*   No code access    
*   Produces atomic subtasks    

### 🔧 **Execution Agent**

*   Converts Subtask → File Edits    
*   Works only on relevant file slices    
*   Strict JSON output    
*   Produces diffs    

### 🩹 **Debug Agent (FixLoop)**

*   Converts Error → Corrected Edits    
*   Works only on error slice + file slice    
*   Strict JSON output    
*   Produces corrected diffs    

### 🧪 **Validation Agent**

*   Converts Repo → Build/Test Result    
*   No model    
*   Produces pass/fail + error slice    

### 🏛️ **Architecture Agent**

*   Converts Repo → Architecture Violations    
*   No model    
*   Produces rule violations    

### 📘 **PR Agent**

*   Converts Plan + Memory → PR Body    
*   No code access    
*   Produces markdown summary    

### 💾 **Memory Agent**

*   Converts RunState → Rehydrated Context    
*   No code access    
*   Produces task/subtask state    

### 🔌 **Integration Agents**

*   ADO MCP    
*   GitHub MCP    
*   Azure MCP    
*   Provide external capabilities
    
These roles form the **agent team**.

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 2 — From Skills to Agents](./1-phase2-overview.md)
 | 
[Phase 2 — Supervisor design >>](./3-phase2-supervisor-design.md)
