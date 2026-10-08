# Agent Skill Routing Guide

> Goal: help agents in BaiCao decide which skill to use first, which one to layer next, and when to move into multi-agent collaboration instead of only reacting after getting stuck.

This guide complements root `AGENTS.md` and `workflow.md`. It answers a narrower question: within BaiCao's repo rules, which workflow or skill family should drive the current task?

For multi-agent collaboration, this file is also the repo-level single source of truth for when to enter multi-agent mode, which collaboration skill to prefer, and when `fork` context inheritance should be the default.

## 1. Core Routing Principles

- Choose **process skills** first, **domain skills** second, then **collaboration / finishing skills**.
- A normal task should usually activate only 2 to 4 primary skills. Do not stack every possible skill.
- If multiple skills match, decide **how to work** before deciding **what to implement**: prefer `brainstorming` / `systematic-debugging` / `writing-plans` before frontend, backend, OpenAI, or docs-specific skills.
- Very small read-only questions, path lookups, or one-shot command checks do not need a full skill chain. Once behavior changes, code edits, multi-step verification, or non-obvious decisions appear, the agent should explicitly choose a skill-driven path.
- Before claiming completion, default to `verification-before-completion`.

## 2. Default Skill Order

### 2.1 Process Skills

Use these first to choose the execution mode for the task.

| Situation | Preferred skill | Why |
|---|---|---|
| New feature, behavior change, scope not fully settled | `brainstorming` | Converge on goal, constraints, and success criteria before implementation |
| Larger task, cross-module work, staged dependencies | `writing-plans` | Break work into executable steps with files, tests, and verification; this is BaiCao's repo-standard task system |
| Long-running work that benefits from resumable tracking | `planning-with-files` | Optional private working-memory files for long sessions; not the repo task source of truth |
| Bug, regression, unclear failure, unstable behavior | `systematic-debugging` | Reproduce, isolate root cause, validate hypotheses before patching |
| Review comments or requested follow-up changes | `receiving-code-review` | Judge whether feedback is valid and what scope it affects |

### 2.2 Domain Skills

After process selection, add the narrowest domain skill that matches the main work area.

| Main scope | Common skills | Use for |
|---|---|---|
| React / Vite / frontend implementation | `frontend-design`, `ui-design-brain` | Building pages, views, graph displays, and polished interface structures |
| React / performance / data flow | `vercel-react-best-practices` | Rendering, state flow, data fetching, React patterns |
| UI polish | `make-interfaces-feel-better`, `baseline-ui` | Visual hierarchy, motion, spacing, typography, overall feel |
| Accessibility | `fixing-accessibility` | Keyboard flow, semantics, labels, focus, contrast |
| Motion stutter / rendering jank | `fixing-motion-performance` | Animation and rendering performance issues |
| Python service / readability-only refactor | `code-simplifier-py` | Behavior-preserving cleanup for maintainability |
| TypeScript / shared types / frontend readability-only refactor | `code-simplifier-ts` | Behavior-preserving cleanup for maintainability |
| OpenAI / LangChain / official product behavior | `openai-docs` | Current official guidance for OpenAI product and API usage |
| Architecture / technical docs / diagrams | `docs-with-mermaid` | Design docs, architecture docs, diagrams, flow explanations |

### 2.3 Collaboration Skills

Use these only when the task is actually suitable for multi-agent or plan-driven execution.

| Situation | Skill | Use for |
|---|---|---|
| Multiple independent subproblems can run in parallel | `dispatching-parallel-agents` | Split by independent domains or non-overlapping write scopes |
| There is already a clear implementation plan | `subagent-driven-development` | Execute plan tasks with workers/reviewers while main agent integrates |
| Plan should be executed sequentially inside the current session | `executing-plans` | Follow plan order with explicit checkpoints |

### 2.4 Finishing Skills

| Situation | Skill | Use for |
|---|---|---|
| Major work finished and a deliberate review pass is needed | `requesting-code-review` | Get another review layer before merge or handoff |
| About to say “done” or prepare final handoff | `verification-before-completion` | Run verification first, then report results |
| User explicitly asks for a commit | `git-commit` | Consistent staging and conventional commit shaping |
| Branch is ready for wrap-up | `finishing-a-development-branch` | Merge / PR / cleanup decisions |
| GitHub PR comments or issue workflow | `gh-address-comments`, `github` | Work through review comments and GitHub state |
| GitHub Actions failure | `gh-fix-ci` | Inspect checks/logs and decide whether a fix is appropriate |

## 3. Recommended Flows By Task Type

### 3.1 New Feature Or Behavior Change

Recommended order:

1. `brainstorming`
2. `writing-plans`（如确需额外私有会话笔记，可附加 `planning-with-files`）
3. `test-driven-development`
4. one narrow domain skill
5. `requesting-code-review`
6. `verification-before-completion`

Typical BaiCao examples:

- new graph query capability, provenance feature, review flow, or chat behavior
- new graph runtime primitive, schema-aware planner, graph exploration agent, or runtime-backed API route
- knowledge payload, verification status, or contract-first work spanning `shared` + `api` + `web`
- a new page, endpoint, importer, or expert workflow

### 3.2 Bug Fix Or Regression Investigation

Recommended order:

1. `systematic-debugging`
2. `test-driven-development`
3. one domain skill if needed
4. `verification-before-completion`

Additional rules:

- Do not patch before reproduction, root-cause evidence, and a validated hypothesis exist.
- If the issue is a hang, blocked thread, or CPU anomaly, add `debug-lldb`.

### 3.3 Frontend Page / Component Work

Recommended order:

1. use `brainstorming` if scope is still soft
2. `frontend-design` or `ui-design-brain`
3. `vercel-react-best-practices`
4. add `baseline-ui` / `make-interfaces-feel-better` when polish matters
5. add `fixing-accessibility` for controls, forms, dialogs, or keyboard flows
6. add `fixing-motion-performance` when animation behavior is part of the task
7. `verification-before-completion`

### 3.4 API / Knowledge-Graph / Provenance Work

Recommended order:

1. use `brainstorming` if contracts or scope are still soft
2. `writing-plans` when the change spans schema, service, and consumer updates
3. `test-driven-development`
4. add the narrowest domain skill actually needed (`openai-docs`, `code-simplifier-py`, `docs-with-mermaid`, etc.)
5. `verification-before-completion`

Additional rules:

- For payload changes, follow `workflow.md` and update contract sources before consumers.
- For the current chat mainline runtime, keep `packages/api/app/services/chat_agent_runtime/` as the execution source of truth. Do not restore `packages/graph_runtime/`. Judgments inside that loop (whether to search, whether evidence is enough, whether a draft can be published) go through TypeSafe `system_one` via the `judge` tool. See `docs/architecture/chat-agent-mcp.md`.
- For OpenAI / LangChain usage questions, prefer `openai-docs` over memory.

### 3.5 Docs, Architecture Notes, Process Documents

Recommended order:

1. `brainstorming` if direction is still open
2. `writing-plans` if the document change spans multiple staged edits
3. `docs-with-mermaid` for structured technical docs and diagrams
4. `verification-before-completion`

### 3.6 Complex Tasks: Default Multi-Agent Route

Recommended order:

1. Use a process skill first to clarify scope and splitting boundaries.
2. Decide whether subproblems are independent enough for multi-agent work.
3. If there are multiple independent domains, prefer `dispatching-parallel-agents`.
4. If there is already a concrete plan, prefer `subagent-driven-development`.
5. If plan execution should stay sequential in the same session, use `executing-plans`.
6. Keep orchestration, integration, conflict handling, and unified verification in the main agent.
7. Before final handoff, run `verification-before-completion`.

Default preferences:

- For complex work, prefer multi-agent collaboration over a single serial implementation path.
- Multi-agent execution is not a separate process outside the skill system; it should normally be entered through collaboration skills.
- When a sub-agent clearly depends on context already converged by the main agent, prefer `fork` context inheritance by default.
- When the task is very narrow, or strict context isolation is more valuable than shared background, prefer a manually curated minimal context instead of `fork`.
- Split sub-agents by independent problem domain or non-overlapping write scope. The main agent remains responsible for final synthesis, verification, and user-facing delivery.

## 4. Quick Decision Checklist

Before starting any non-trivial task, quickly ask:

1. Is this a new feature, a behavior change, or a bug fix?
2. Is the scope already clear, or should `brainstorming` happen first?
3. Will this span multiple stages or modules, making `writing-plans` appropriate as the repo task system?
4. Is the main scope frontend, backend, shared contract, data / graph, docs, OpenAI integration, review flow, or CI?
5. Is there obvious risk that requires `systematic-debugging` or `receiving-code-review` first?
6. What is the narrowest domain skill that actually helps this task?
7. What verification is required before entering `verification-before-completion`?

If two or more of these questions point to staged execution, the task should not be handled as ad-hoc implementation.

## 5. Anti-Patterns

- Do not skip process skills just because the task “looks small”.
- Do not activate multiple overlapping domain skills without a clear gap each one fills.
- Do not patch a bug before evidence supports the fix direction.
- Do not use `dispatching-parallel-agents` on strongly sequential or tightly coupled work.
- Do not outsource critical-path reasoning too early when the main agent is still the bottleneck.
- Do not parallelize sub-agents that will edit the same write scope.
- Do not treat `verification-before-completion` as optional.

## 6. Relationship To BaiCao Workflow

- Primary scope selection, source-of-truth rules, and cross-module sequencing come from root `workflow.md`.
- Project positioning and current-stage context come from `README.md` and the relevant `docs/plans/` files.
- This file solves one narrower problem: within those repo rules, which skill-driven route should the agent choose first?

One-line version:

Choose the method before the implementation, control risk before widening scope, and verify before claiming completion.
