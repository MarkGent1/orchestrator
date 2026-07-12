# 3.2 Phase 3 — Folder Structure

```
orchestrator/
    agents/
        base/
        planning_agent.py
        decomposition_agent.py
        execution_agent.py
        fixloop_agent.py
        validation_agent.py
        pr_agent.py
        architecture_agent.py
        messaging/
            agent_message.py
            message_bus.py
            inbox.py
            outbox.py
        reflection/
            reflection_policy.py
            reflection_loop.py

    supervisor/
        supervisor_agent.py
        parallel/
            worker_pool.py
            task_scheduler.py
            dependency_graph.py

    metrics/
        agent_metrics.py
        metrics_collector.py
        timeline.py

    dashboard/
        renderer.py
        web/
            server.py
            templates/
                index.html
                timeline.html
                architecture.html
```

[<< Roadmap for advancing AI Engineering Practices](../1-roadmap-overview.md)
 | 
[<< Phase 3 — Components](./2-phase3-components.md)
 | 
[Phase 3 — Implementation Plan >>](./4-phase3-implementation-plan.md)
