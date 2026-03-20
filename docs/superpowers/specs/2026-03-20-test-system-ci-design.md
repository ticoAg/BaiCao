# BaiCao Test System And GitHub Actions Design

## 1. Summary

This spec defines the first complete testing system for BaiCao ShiTan.

The goal is to turn the current collection of local scripts, backend tests, frontend tests, Playwright smoke coverage, and acceptance documents into one coherent system with:

- strong layer definitions
- one canonical way to run validation from the repo root
- a GitHub Actions pipeline with fast and slow required checks
- clear separation between local realism and CI lightness

This spec is intentionally scoped to testing and CI only. It does not cover release orchestration, deployment policy, or full environment governance.

## 2. Scope

### In Scope

- test layer definitions for backend, frontend, browser smoke, and acceptance
- backend test directory migration to explicit layer-based structure
- unified root-level test and verification commands
- GitHub Actions design for fast and slow required checks
- minimum acceptance document set for major user-facing flows
- completion criteria for the testing system

### Out Of Scope

- release workflows
- deployment workflows
- nightly or scheduled jobs
- full environment parity between local and CI
- broad production observability and quality governance

## 3. Constraints And Decisions

The user approved the following constraints:

- platform target: GitHub Actions
- gate strategy: layered gates
- CI dependency policy: lightweight mode
- compatibility strategy: no backward-compatibility requirement for the old test structure

Implications:

- local development may remain more realistic than CI
- CI should avoid always booting PostgreSQL, Neo4j, and Redis
- backend tests can be physically reorganized now instead of keeping legacy paths
- E2E remains required, but as a separate slower check

## 4. Target Test Architecture

The target testing system has five layers.

### 4.1 Unit

Purpose:

- verify internal logic, classification, formatting, mapping, and edge cases

Rules:

- must not require real PostgreSQL, Neo4j, Redis, or browser runtime
- should run quickly
- should fail only because business logic changed

Examples:

- service logic
- graph response mapping
- provenance formatting logic
- frontend page/component behavior with mocked API calls

### 4.2 Contract

Purpose:

- verify API protocol and response shape

Rules:

- may mock lower layers
- must exercise request parsing, status codes, response payload structure, and error semantics
- must not silently drift from real API contracts

Examples:

- FastAPI route tests
- health check route
- validation and error-path protocol tests

### 4.3 Integration

Purpose:

- verify application behavior against real dependencies

Rules:

- must use real services or real spawned application processes
- cannot be "all mocked" while still being called integration

Phase-one policy:

- this layer is formally defined and given a stable home
- it is not part of the default GitHub Actions required gate in this phase

### 4.4 End-To-End

Purpose:

- verify real browser mainline flows across pages and APIs

Rules:

- must be minimal and high-value
- should validate critical user journeys, not every UI detail
- should use robust selectors and business-meaningful assertions

Phase-one policy:

- one stable smoke mainline is required

### 4.5 Acceptance

Purpose:

- prove a feature is actually deliverable

Rules:

- each document must define scope, prerequisites, steps, expected result, evidence, and conclusion
- this layer is documentation-backed verification, not only code-based testing

## 5. Execution Model

### 5.1 Local

Canonical root commands:

- `pnpm run demo`
- `pnpm run test:api`
- `pnpm run test:web`
- `pnpm run test:e2e`
- `pnpm run verify`
- `pnpm run verify:full`

Expected behavior:

- developers and agents should not need to memorize package-specific commands
- docs, scripts, and CI should point to the same command set

### 5.2 CI

The system deliberately separates local realism from CI speed.

Local:

- may use tmux, demo seed data, and real support services

CI:

- should prefer lightweight checks by default
- should only run the smallest necessary browser smoke path
- should not default to full real-service orchestration in every PR

## 6. File And Directory Structure

### 6.1 Root

- `package.json`
  - canonical script entrypoint
- `playwright.config.ts`
  - browser smoke configuration
- `.github/workflows/`
  - GitHub Actions workflow definitions
- `tests/e2e/`
  - browser mainline smoke tests
- `scripts/`
  - executable test orchestration scripts
- `docs/acceptance/`
  - executable acceptance documents

### 6.2 Backend Test Layout

Target structure:

- `packages/api/tests/conftest.py`
- `packages/api/tests/README.md`
- `packages/api/tests/unit/`
- `packages/api/tests/contract/`
- `packages/api/tests/integration/`

Directory migration:

- `packages/api/tests/api/` -> `packages/api/tests/contract/`
- `packages/api/tests/services/` -> `packages/api/tests/unit/services/`
- `packages/api/tests/kg/` -> `packages/api/tests/unit/kg/`
- `packages/api/tests/溯源/` -> `packages/api/tests/unit/provenance/`
- `packages/api/tests/test_health.py` -> `packages/api/tests/contract/test_health.py`

Principles:

- directory names must directly express testing layer
- no compatibility alias directories
- no mixed-language test paths

### 6.3 Frontend Test Layout

Target structure:

- `packages/web/src/**/*.test.tsx`
- `packages/web/src/test/setup.ts`
- `packages/web/src/test/render-with-providers.tsx`

Principles:

- keep tests close to pages/components
- centralize shared provider bootstrapping and jsdom shims
- do not introduce a heavy extra frontend test directory if colocated tests remain clear

## 7. GitHub Actions Design

Two workflows are required.

### 7.1 `ci-fast.yml`

Triggers:

- `pull_request`
- `push` to protected primary branch

Jobs:

- `api-tests`
  - install Python and `uv`
  - run the backend fast suite through `./scripts/test_api.sh`
  - scope: unit + contract

- `web-tests`
  - install Node and `pnpm`
  - run `pnpm run test:web`
  - optionally run `pnpm --dir packages/web build`

Characteristics:

- fast feedback
- no default startup of PostgreSQL, Neo4j, or Redis
- required for merge

### 7.2 `ci-e2e.yml`

Triggers:

- `pull_request`

Job:

- `e2e-smoke`
  - install Node and `pnpm`
  - install Playwright browser
  - run `./scripts/test_e2e.sh`

Characteristics:

- slower but required
- validates the minimum real browser mainline
- remains intentionally small in scope

### 7.3 Required Checks

Required GitHub checks:

- `ci-fast / api-tests`
- `ci-fast / web-tests`
- `ci-e2e / e2e-smoke`

Meaning:

- fast gates provide quick developer feedback
- the slow browser gate provides additional confidence
- all three are merge-blocking in phase one

## 8. Migration Strategy

Migration should be direct, not compatibility-first.

### 8.1 Backend

- physically move tests into `unit`, `contract`, and `integration`
- update imports and file paths accordingly
- keep `conftest.py` at the test root
- keep pytest markers aligned with physical directory intent

### 8.2 Frontend

- keep colocated page tests
- expand from current page coverage instead of redesigning the whole frontend structure

### 8.3 Integration

First-phase integration assets should remain minimal:

- one graph query real-dependency smoke
- one verification create/approve/sync real-dependency smoke

Integration exists as a first-class layer, but it is intentionally not yet a required CI gate.

## 9. Testing Standards

### 9.1 Layer Rules

- every backend test file belongs to exactly one layer
- `unit` cannot depend on real external services
- `contract` cannot obscure API semantics
- `integration` must involve real dependencies
- `e2e` must verify cross-page user journeys, not micro-details

### 9.2 Script Rules

- every standard validation path must be runnable from repo root
- scripts must be non-interactive and repeatable
- docs and CI must reference the same command names

### 9.3 Gate Rules

- required checks cannot be bypassed as a normal workflow
- test fragility must be fixed by improving selectors or assertions, not by downgrading the gate
- if integration remains unstable, it stays outside required CI until hardened

## 10. Definition Of Done

The testing system is considered established when all of the following are true:

- root test entrypoints exist and are documented
- backend tests are physically migrated into explicit layers
- frontend test stack is stable and covers core pages
- at least one stable Playwright mainline smoke exists
- at least three executable acceptance documents exist
- GitHub Actions fast and slow workflows are defined
- required check names are explicit and consistent with the workflow design

## 11. Risks

- frontend library warnings in jsdom can add test noise even when behavior is correct
- backend mock-heavy legacy tests may hide real integration issues until integration coverage grows
- E2E can become brittle if selector discipline weakens
- CI remains intentionally lighter than local, so some real-dependency regressions still depend on local verification until the integration layer is expanded

## 12. Recommendation

Proceed with a direct migration to the target structure and implement phase one in this order:

1. backend test directory migration
2. root script normalization
3. frontend unit testing stabilization
4. GitHub Actions workflow introduction
5. first stable E2E smoke
6. acceptance document completion

This keeps the system coherent from the beginning instead of accumulating another transitional layer.
