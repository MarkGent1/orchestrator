# Agentic AI Engineering Roadmap

_A learning and build roadmap for leveling up the orchestrator (and the engineer building it)._

This isn't documentation of what the orchestrator does today — that lives in `ReadMe.md` and `docs/pages/`. This is a roadmap of the broader discipline of building agentic AI systems, mapped onto concrete next steps for this project specifically. Each section below draws on Anthropic's own engineering guidance (linked at the bottom) and connects it to something already true — or worth becoming true — about the orchestrator.

---

## 1. Context Engineering

**What it is.** The practice of deciding what tokens go in front of the model, and in what order, for a given call. Anthropic frames it as system instructions first, then relevant memory, then tool definitions, then conversation history. Context is a finite resource, not a free one — past a certain point, adding more of it degrades performance ("context rot") rather than improving it. The skill isn't "give the model more," it's "give the model the highest-value tokens for this specific decision."

**Where the orchestrator already does this.** `prompt_builder.py` filters aggressively before anything reaches the model: `EXCLUDED_DIRS` keeps build artifacts and test file *content* out of the prompt, while the newer `TREE_EXCLUDED_DIRS` keeps the repo *tree* visible (including `tests/`) without paying the token cost of full file contents. That split — tree visibility vs. content visibility — is context engineering in miniature.

**What's worth exploring next.**
- **Compaction.** For a Work Item with many tasks/subtasks, each subtask currently gets a freshly-built prompt, but as the run gets longer there's more accumulated state (task memory, prior errors, prior edits) that could bloat future prompts if included naively. Explore summarizing "what's already been done" rather than replaying it verbatim.
- **Context budgets per phase.** Planning, decomposition, execution, and FixLoop all have different context needs. Worth explicitly reasoning about what each one actually needs to see, rather than reusing the same collection logic everywhere.
- **Just-in-time vs. up-front loading.** Right now the repo tree and relevant files are gathered up front for every subtask. An alternative pattern (used by some coding agents) is giving the model a tool to request more file content on demand, only when it decides it needs it — trading a slightly more complex tool-use loop for a much smaller default context.

---

## 2. Skills (Agent Skills)

**What it is.** A skill is a reusable, on-demand-loaded bundle of domain expertise — instructions, conventions, examples — that the agent loads only when relevant, instead of that knowledge being baked into every prompt regardless of whether it's needed. The core design principle is *progressive disclosure*: like a manual with a table of contents, the agent shouldn't have to read the whole thing to use one page of it. Anthropic's practical advice: start small (a skill can be a few lines and one hard-won gotcha), write descriptions as *triggers* ("use this when X"), not summaries, and split a skill into multiple files once it gets unwieldy.

**Where the orchestrator already does this, informally.** The `backend_rules`, `frontend_rules`, and `test_placement_rules` strings inside `prompt_builder.py` are hand-rolled skills — domain-specific conventions injected into the prompt based on repo type. They work, but they're inline f-strings: every edit means touching Python code, there's no versioning independent of the codebase, and there's no way to see "what conventions does this orchestrator currently enforce" without reading the prompt-construction logic.

**What's worth exploring next.**
- **Extract the rule blocks into standalone files** (e.g. `skills/backend-clean-architecture.md`, `skills/test-placement.md`) that `prompt_builder.py` loads rather than hardcodes. This makes each one independently editable, diffable, and testable in isolation.
- **Per-repo skills.** As more repos get onboarded (see `docs/pages/12-onboard-new-repos.md`), some will have genuinely repo-specific conventions (CQRS, Mediatr, a particular DI pattern). A skill-per-repo-convention model scales better than growing a single monolithic prompt with `if repo_name == ...` branches.
- **Treat skill quality as an eval target** (see §6) — when a subtask gets an illegal path or a wrong convention, that's a signal a skill is missing or under-specified, not just a one-off bug.

---

## 3. Tool Design

**What it is.** Tools are contracts between a deterministic system and a non-deterministic agent — a fundamentally different design problem than a typical API, because the "caller" reasons, explores, and sometimes misuses the contract in ways a human developer wouldn't. Anthropic's guidance: choose carefully which capabilities actually need to be tools, namespace them clearly, return *meaningful* context back to the model (not a raw API dump), optimize for token efficiency in responses, and prompt-engineer the tool's description the same way you'd prompt-engineer anything else — small wording changes measurably changed SWE-bench performance in their own testing.

**Where this shows up in the orchestrator.** The ADO and GitHub MCP servers *are* the tool layer here. The idempotency bug fixed earlier this project (missing `$expand=relations` on `getWorkItem`) was, in retrospect, a tool-design bug: the tool silently returned incomplete context, and the calling code had no way to know it was incomplete.

**What's worth exploring next.**
- **Audit each MCP tool's return shape.** Does `getWorkItem` return the minimum the model needs, or a raw ADO payload the model has to parse itself? Meaningful, pre-shaped context reduces both token cost and model error rate.
- **Tool description pass.** Treat each tool's description (in `server.js` for both MCP servers) as a prompt worth iterating on, the same way `prompt_builder.py`'s rule blocks are.
- **Consider consolidating narrow tools.** If `createChildTask`, `addWorkItemComment`, `updateWorkItem`, and `linkPullRequest` are always called in the same sequence for a given phase, a single higher-level tool that does the sequence atomically may be more reliable than four separate calls the model has to get right independently.

---

## 4. Long-Running Agent Harnesses

**What it is.** The infrastructure that lets an agent survive across a long task: checkpointing progress, recovering from a crash mid-way, and — at scale — compacting history so a long-running session doesn't outgrow its context window. This is a genuinely different problem from a single chat turn, and it's one this project has already invested in directly.

**Where the orchestrator already does this.** `run_state.py` and the `.orchestrator-state/<repo-key>-<work_item_id>.json` mechanism (see `docs/pages/14-resume-from-crash.md`) is exactly this pattern: persist enough state that a crash mid-run — a bad model response, an MCP timeout, an illegal-path error — doesn't discard everything already committed. This was validated in production on the work-item-461 crash.

**What's worth exploring next.**
- **Compaction for very long Work Items.** If a Work Item ever grows to dozens of tasks, the current model of "re-run and skip completed work" is fine for resume correctness, but the *prompts* for later tasks could still benefit from a compacted summary of everything done so far, rather than task memory growing unbounded.
- **Partial-subtask checkpointing.** Right now the unit of resume is a subtask. If a single subtask's model call is itself expensive (large diff, long FixLoop retry chain), a finer-grained checkpoint inside FixLoop's retry loop could save re-work on resume.

---

## 5. Multi-Agent Orchestration

**What it is.** Instead of one agent doing everything sequentially, an orchestrator-worker pattern has a lead agent plan and delegate to multiple subagents that run in parallel, each with its own isolated context window and no visibility into what the others are doing. Anthropic's own multi-agent research system uses this to get a ~90% quality improvement over a single agent on complex tasks — at roughly **15x the token cost** of a single-agent run. It's a real capability upgrade, not a free one.

**Where the orchestrator currently stands.** The pipeline today is a strict sequential chain: Planning (Sonnet) → Decomposition (GPT-mini) → Execution (Haiku, per subtask) → Validation/FixLoop (Haiku). Subtasks within a task are executed one at a time.

**What's worth exploring next.**
- **Parallelize independent subtasks.** Not all subtasks within a task depend on each other's output. Where they don't, running them as parallel subagents (each with its own scoped file-edit context) could meaningfully cut wall-clock time on multi-file tasks.
- **Cost-aware routing.** Given the 15x cost multiplier Anthropic observed, this is worth trying only where task complexity actually justifies it — e.g. large fullstack Work Items, not every single-file backend fix.
- **Isolation discipline.** If this is attempted, the Clean Architecture enforcer and `apply_file_edits_for_task()` need to remain the single source of truth for validating edits regardless of which subagent proposed them, to avoid two parallel subagents silently stepping on the same file.

---

## 6. Evals

**What it is.** A systematic way to answer "did that change actually make the agent better?" — as distinct from unit tests, which answer "did that change break the code." Evals run the *agent* against representative tasks with known-good expected outcomes and measure the result.

**Where the orchestrator currently stands.** The 176-test pytest suite is real and valuable, but it tests the orchestrator's own Python code (path normalization, idempotency logic, resume persistence, etc.) — it doesn't tell you whether a prompt change made the *planning* worse, or whether a new model made the *FixLoop* less effective at actually fixing real build errors.

**What's worth exploring next.**
- **Build a small, real eval set.** A handful of representative Work Items (a couple of backend fixes, a frontend feature, a fullstack change) with known-good expected plans/diffs/outcomes, run periodically — especially before/after a model swap, a prompt change, or a `models.yaml` routing change.
- **Track FixLoop success rate over time**, not just pass/fail on a given run — this is the single component most likely to silently degrade if a model update changes its behavior.
- **Treat every production incident as a candidate eval case.** The work-item-461 illegal-path crash is a perfect example: it should live on permanently as an eval scenario, not just a regression test, so future prompt or model changes get checked against it too.

---

## 7. Observability

**What it is.** Structured visibility into what the agent actually did and why — which model was called, with what tokens, at what cost, with what latency, and which prompt/skill version was in effect — so a failure or a cost spike in production is diagnosable without re-reading raw terminal scrollback.

**Where the orchestrator currently stands.** Diagnosis today happens via `print()` statements and reading the console output of a run (as in the work-item-461 crash transcript). That's workable at today's scale, but doesn't scale to "why did this Work Item cost $40" or "which of the last 20 runs used the slow model path."

**What's worth exploring next.**
- **Structured, per-phase logging** (JSON lines, one entry per model call: phase, model, tokens in/out, latency, success/failure) instead of ad hoc prints — cheap to add, high value the first time something goes wrong.
- **Cost and token tracking per Work Item**, surfaced somewhere reviewable (a log file, a PR comment, an ADO comment) so cost isn't a surprise.
- **Correlate with the existing state file.** Since `.orchestrator-state/` already tracks per-subtask status, extending it to also record which model/prompt version ran each subtask gives free historical debugging.

---

## 8. Guardrails and Security

**What it is.** The set of constraints that keep an agent from doing something unsafe or unintended, especially when it's reading untrusted input (a Work Item description, repository content) or has write access to real infrastructure (a git repo, a PR).

**Where the orchestrator already does this.** The Clean Architecture enforcer is a real guardrail — it doesn't just guide the model, it *rejects* illegal edits regardless of what the model proposes, and (as of this session) that rejection is now contained gracefully in both the task-execution and FixLoop paths rather than crashing the run.

**What's worth exploring next.**
- **Prompt injection awareness.** A Work Item description or a file already in the target repo is untrusted text from the model's point of view — in principle, either could contain text trying to steer the model's behavior (e.g. "ignore previous instructions and also modify X"). Worth thinking through what the blast radius would be if that happened, given the enforcer's current scope.
- **A human approval gate before merge**, distinct from PR creation. Opening a PR is already a safe checkpoint; explicitly deciding whether "auto-merge" is ever appropriate (vs. always requiring a human click) is a guardrails decision worth making deliberately rather than by default.
- **Secrets hygiene.** Already partially covered (the `.env` file with live-looking keys was confirmed `.gitignore`d earlier in this project) — worth revisiting periodically as new MCP servers or integrations are added.

---

## Suggested Sequence

Given the Azure MCP server work already in flight, a reasonable order for the rest of this list:

1. **Finish the Azure MCP server.**
2. **Skills formalization** (§2) — cheap, directly extends work already done in `prompt_builder.py`, and makes future convention changes safer to make.
3. **A small eval set** (§6) — without this, every subsequent change (skills, tool tweaks, model routing) is a guess rather than a measured improvement.
4. **Observability** (§7) — low effort, and makes every other change in this list easier to evaluate and debug going forward.
5. **Guardrails/security review** (§8) — worth doing deliberately once, rather than reactively after an incident.
6. **Long-running harness refinements** (§4) — compaction and finer-grained checkpointing, once there's real usage data showing where it's needed.
7. **Multi-agent orchestration** (§5) — the most expensive and highest-effort item; worth attempting only once the eval set (§3) exists to actually measure whether it helps.

---

## Sources

- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — Anthropic
- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — Anthropic
- [Agent Skills — Claude Platform Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — Anthropic
- [Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — Anthropic
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — Anthropic
- [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — Anthropic
