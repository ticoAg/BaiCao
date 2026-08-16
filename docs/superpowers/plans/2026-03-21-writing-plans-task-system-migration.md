# BaiCao Writing-Plans Task System Migration Implementation Plan

> **Status:** done。`IMPL_PLAN.md` / `.task/` 已删除；任务真源是 `docs/superpowers/plans/`。不要再执行。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Remove BaiCao's custom `.task/` and `TODO_LIST.md` task system and make `writing-plans` output under `docs/superpowers/plans/` the only repo-level implementation task system.

**Architecture:** Keep `IMPL_PLAN.md` as high-level product/stage planning, keep `docs/superpowers/specs/` for design specs, and promote `docs/superpowers/plans/` to the single source of truth for executable task breakdown and progress tracking. Update every repo-level guide that currently points to `.task/`, add a `docs/superpowers/README.md` entry portal, and delete the obsolete custom task files.

**Tech Stack:** Markdown documentation, repo workflow docs, superpowers `writing-plans`

---

## Target File Map

### Documentation And Workflow Entrypoints

- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `workflow.md`
- Modify: `IMPL_PLAN.md`
- Modify: `docs/README.md`
- Modify: `docs/agent-skill-routing.md`
- Modify: `docs/verification-matrix.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/acceptance/README.md`
- Modify: `docs/acceptance/template.md`
- Modify: `docs/acceptance/chat-mainline.md`
- Modify: `docs/acceptance/graph-workbench-mainline.md`
- Modify: `docs/acceptance/verification-workflow.md`
- Create: `docs/superpowers/README.md`
- Create: `docs/superpowers/plans/2026-03-21-writing-plans-task-system-migration.md`

### Removal

- Delete: `.task/IMPL-001-project-skeleton.json`
- Delete: `.task/IMPL-002-backend-core.json`
- Delete: `.task/IMPL-003-frontend-core.json`
- Delete: `.task/IMPL-004-knowledge-graph.json`
- Delete: `.task/IMPL-005-chat-visualization.json`
- Delete: `.task/IMPL-006-infrastructure.json`
- Delete: `TODO_LIST.md`

### Verification

- Test: repo-wide reference check with `rg`
- Test: path existence for `docs/superpowers/README.md` and plan docs

## Task 1: Establish `docs/superpowers/` As The New Task System Portal

**Files:**
- Create: `docs/superpowers/README.md`
- Modify: `docs/README.md`
- Test: link and terminology consistency

- [x] **Step 1: Add a dedicated superpowers portal**

Create `docs/superpowers/README.md` that explains:

- `specs/` stores design specs
- `plans/` stores executable implementation plans
- `writing-plans` is the repo-standard task system
- `subagent-driven-development` and `executing-plans` are execution follow-ups

- [x] **Step 2: Point the main docs portal to the new portal**

Update `docs/README.md` so task and plan references point to `docs/superpowers/README.md` and `docs/superpowers/plans/`, not `.task/`.

- [x] **Step 3: Clarify planning ownership**

Document that:

- `IMPL_PLAN.md` is high-level planning only
- `docs/superpowers/specs/` is design intent
- `docs/superpowers/plans/` is executable task truth

## Task 2: Update Repo-Wide Workflow And Source-Of-Truth References

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `workflow.md`
- Modify: `docs/agent-skill-routing.md`
- Modify: `docs/verification-matrix.md`
- Modify: `docs/architecture/README.md`
- Modify: `docs/acceptance/README.md`
- Modify: `IMPL_PLAN.md`
- Test: `rg -n "\.task|TODO_LIST|IMPL-00|任务真源|任务状态来源" AGENTS.md README.md workflow.md docs IMPL_PLAN.md`

- [x] **Step 1: Replace `.task/` as repo task SSOT**

Change all repo-level wording that says `.task/` is the task source of truth so it instead points to `docs/superpowers/plans/*.md`.

- [x] **Step 2: Make `writing-plans` explicit in routing**

Update `docs/agent-skill-routing.md` so repo-standard staged work uses `writing-plans`, while any mention of `planning-with-files` is clearly optional and not the repo task truth.

- [x] **Step 3: Re-scope `IMPL_PLAN.md`**

Keep the current high-level phase roadmap, but explicitly mark it as high-level planning rather than the live task tracker.

- [x] **Step 4: Re-scope acceptance references**

Update acceptance docs and templates so they refer to corresponding plan/spec documents instead of deleted custom task ids.

## Task 3: Remove The Custom Task System Files

**Files:**
- Delete: `.task/`
- Delete: `TODO_LIST.md`
- Test: `test ! -e .task && test ! -e TODO_LIST.md`

- [x] **Step 1: Delete obsolete custom task files**

Remove the `.task/` JSON files and `TODO_LIST.md` after all references are migrated.

- [x] **Step 2: Verify there are no stale references**

Run a repo-wide `rg` search to ensure the deleted system is no longer referenced by the maintained docs.

## Task 4: Run Documentation Verification

**Files:**
- Test: documentation and reference consistency only

- [x] **Step 1: Check for stale task-system references**

Run:

```bash
rg -n "\.task|TODO_LIST|IMPL-00" AGENTS.md README.md workflow.md docs IMPL_PLAN.md
```

Expected:

- no maintained-doc references remain to the removed custom task system
- any remaining matches are historical text that is intentionally preserved or absent

- [x] **Step 2: Check new portal references**

Run:

```bash
rg -n "docs/superpowers/README.md|docs/superpowers/plans|writing-plans" AGENTS.md README.md workflow.md docs IMPL_PLAN.md
```

Expected:

- repo entry docs consistently point to the new task system

- [x] **Step 3: Commit**

```bash
git add AGENTS.md README.md workflow.md IMPL_PLAN.md docs/README.md docs/agent-skill-routing.md docs/verification-matrix.md docs/architecture/README.md docs/acceptance/README.md docs/acceptance/template.md docs/acceptance/chat-mainline.md docs/acceptance/graph-workbench-mainline.md docs/acceptance/verification-workflow.md docs/superpowers/README.md docs/superpowers/plans/2026-03-21-writing-plans-task-system-migration.md
git rm -r .task TODO_LIST.md
```
