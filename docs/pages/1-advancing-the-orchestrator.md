# Advancing the Orchestrator

The orchestrator has now evolved into a **full autonomous SDLC engine**:

> “AI reads the Work Item → plans → branches → edits → builds → tests → fixes → commits → PR → links → updates.”

It now performs real development work, real validation, and real PR automation — safely, deterministically, and repeatably.

## 1. Work Item → Plan → Tasks

This is the **outer loop brain**.

The orchestrator now:

*   Reads the Work Item from Azure DevOps via MCP    
*   Extracts:
    *   Title        
    *   Description        
    *   Acceptance Criteria        
    *   Tags        
    *   Area Path        
    *   Iteration Path        
*   Validates Work Item quality    
*   Generates a structured task plan    
*   Creates child tasks in ADO    
*   Adds a comment summarising the plan    
*   Updates the Work Item state → **Active**    
*   Returns the plan to the orchestrator core

## 2. Branch + PR automation

This is the **AI developer loop** — the “hands”.

The orchestrator now:

*   Creates a feature branch    
*   Copies the repo into a **temp workspace**    
*   Detects repo type (backend/frontend)    
*   Decomposes tasks into subtasks    
*   Builds repo‑aware prompts    
*   Calls OpenCode (Claude) for file edits    
*   Applies edits safely (no corruption, no hallucinated folders)    
*   Commits each subtask atomically    
*   Runs build + tests    
*   Auto‑fixes failures via FixLoop    
*   Pushes the branch    
*   Opens a PR    
*   Enhances the PR description    
*   Links the PR to the Work Item

## 3. Azure deployment integration

Once the Azure MCP server is added, the orchestrator will be able to:

*   Deploy to TEST    
*   Run smoke tests    
*   Tear down environments    
*   Fetch logs    
*   Update the Work Item with deployment results
    
This becomes the “legs” of the system.

## 4. Full SDLC loop

When all modules are connected:

1.  You say: **“Implement feature X”**    
2.  Orchestrator does:
    *   Read Work Item        
    *   Validate acceptance criteria        
    *   Generate plan        
    *   Create tasks        
    *   Create branch        
    *   Modify files        
    *   Commit        
    *   Push        
    *   PR        
    *   Link PR        
    *   Update Work Item        
    *   Deploy        
    *   Tear down        
    *   Close Work Item
        
This is the **autonomous SDLC engine**.

[<< Overview](../../README.md)
 | 
[Module 1: Work Item + Plan + Tasks >>](./2-module-1.md)
