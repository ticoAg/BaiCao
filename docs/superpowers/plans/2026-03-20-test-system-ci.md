# BaiCao Test System And GitHub Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganize BaiCao's tests into explicit layers, add real integration scaffolding, and ship a GitHub Actions CI setup with fast required checks plus a separate required E2E smoke gate.

**Architecture:** Keep local development realistic and CI lightweight. The repo root remains the canonical execution surface, backend tests are physically migrated into `unit / contract / integration`, frontend tests stay colocated with pages, and GitHub Actions consumes the same root scripts as developers. E2E stays intentionally small and high-value, while integration becomes a first-class layer without entering the default CI gate yet.

**Tech Stack:** Python 3.12+, `uv`, `pytest`, `pytest-asyncio`, FastAPI, React 18, Vitest, Testing Library, Playwright, pnpm, GitHub Actions

---

## Target File Map

### Root Orchestration

- Modify: `package.json`
- Modify: `scripts/test_api.sh`
- Create: `scripts/test_integration.sh`
- Modify: `scripts/test_e2e.sh`
- Modify: `scripts/start_demo_tmux.sh`

### Backend Test Layout

- Modify: `packages/api/pyproject.toml`
- Modify: `packages/api/tests/conftest.py`
- Modify: `packages/api/tests/README.md`
- Create: `packages/api/tests/unit/services/test_chat_service.py`
- Create: `packages/api/tests/unit/kg/test_graph_service.py`
- Create: `packages/api/tests/unit/provenance/test_provenance.py`
- Create: `packages/api/tests/contract/test_routes.py`
- Create: `packages/api/tests/contract/test_verification.py`
- Create: `packages/api/tests/contract/test_health.py`
- Create: `packages/api/tests/integration/conftest.py`
- Create: `packages/api/tests/integration/test_graph_search_smoke.py`
- Create: `packages/api/tests/integration/test_verification_sync_smoke.py`
- Delete after migration: `packages/api/tests/api/test_routes.py`
- Delete after migration: `packages/api/tests/api/test_verification.py`
- Delete after migration: `packages/api/tests/kg/test_graph_service.py`
- Delete after migration: `packages/api/tests/services/test_chat_service.py`
- Delete after migration: `packages/api/tests/test_health.py`
- Delete after migration: `packages/api/tests/溯源/test_provenance.py`

### CI

- Create: `.github/workflows/ci-fast.yml`
- Create: `.github/workflows/ci-e2e.yml`

### Documentation

- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/acceptance/README.md`
- Modify: `docs/acceptance/graph-query-mainline.md`
- Modify: `docs/acceptance/chat-mainline.md`
- Modify: `docs/acceptance/verification-workflow.md`

## Task 1: Normalize Root Test Commands And Script Semantics

**Files:**
- Modify: `package.json`
- Modify: `scripts/test_api.sh`
- Create: `scripts/test_integration.sh`
- Modify: `scripts/test_e2e.sh`
- Modify: `scripts/start_demo_tmux.sh`
- Test: root command surface via `pnpm run test:api`, `pnpm run test:web`, `pnpm run test:e2e`, `pnpm run verify`, `pnpm run verify:full`

- [ ] **Step 1: Write the failing behavior note in the plan branch**

Create a scratch checklist in the commit message draft or local notes:

```text
- test:api must exclude integration
- test:integration must exist explicitly
- test:e2e must work in CI without tmux dependency
- verify and verify:full must keep one canonical command surface
```

- [ ] **Step 2: Make `test:api` explicitly fast-gate only**

Update `scripts/test_api.sh` to:

```bash
uv run python -m pytest -q -m "unit or contract"
```

Expected effect:

- root fast validation no longer accidentally starts running integration once that layer exists

- [ ] **Step 3: Add a dedicated integration entrypoint**

Create `scripts/test_integration.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT/packages/api"
uv sync --extra dev
uv run python -m pytest -q -m "integration"
```

- [ ] **Step 4: Refactor `test:e2e` so it supports CI light mode**

Update `scripts/test_e2e.sh` so it can:

- reuse existing local services if already running
- avoid requiring `tmux` inside GitHub Actions
- launch API and Web directly in background when `CI=true`

Recommended structure:

```bash
if [ "${CI:-}" = "true" ]; then
  # launch API and Web in background with logs
else
  # current local/demo path
fi
```

- [ ] **Step 5: Keep `start_demo_tmux.sh` local-focused**

Ensure `scripts/start_demo_tmux.sh` stays responsible only for:

- local demo startup
- seeding demo data
- opening long-running services in tmux

Do not make CI depend on tmux.

- [ ] **Step 6: Wire the new command into root `package.json`**

Modify root scripts to include:

```json
"test:integration": "./scripts/test_integration.sh"
```

Keep:

- `test:api`
- `test:web`
- `test:e2e`
- `verify`
- `verify:full`

- [ ] **Step 7: Run the root commands and verify semantics**

Run:

```bash
pnpm run test:api
pnpm run test:web
```

Expected:

- both PASS
- integration tests are not included in `test:api`

- [ ] **Step 8: Commit**

```bash
git add package.json scripts/test_api.sh scripts/test_integration.sh scripts/test_e2e.sh scripts/start_demo_tmux.sh
git commit -m "build: normalize test command semantics"
```

## Task 2: Physically Migrate Backend Tests Into Explicit Layers

**Files:**
- Modify: `packages/api/pyproject.toml`
- Modify: `packages/api/tests/conftest.py`
- Modify: `packages/api/tests/README.md`
- Create: `packages/api/tests/unit/services/test_chat_service.py`
- Create: `packages/api/tests/unit/kg/test_graph_service.py`
- Create: `packages/api/tests/unit/provenance/test_provenance.py`
- Create: `packages/api/tests/contract/test_routes.py`
- Create: `packages/api/tests/contract/test_verification.py`
- Create: `packages/api/tests/contract/test_health.py`
- Delete: legacy files under `packages/api/tests/api`, `packages/api/tests/kg`, `packages/api/tests/services`, `packages/api/tests/溯源`, and `packages/api/tests/test_health.py`
- Test: `./scripts/test_api.sh`

- [ ] **Step 1: Create the target directories**

Run:

```bash
mkdir -p packages/api/tests/unit/services
mkdir -p packages/api/tests/unit/kg
mkdir -p packages/api/tests/unit/provenance
mkdir -p packages/api/tests/contract
mkdir -p packages/api/tests/integration
```

- [ ] **Step 2: Move the contract files**

Run:

```bash
mv packages/api/tests/api/test_routes.py packages/api/tests/contract/test_routes.py
mv packages/api/tests/api/test_verification.py packages/api/tests/contract/test_verification.py
mv packages/api/tests/test_health.py packages/api/tests/contract/test_health.py
```

- [ ] **Step 3: Move the unit files**

Run:

```bash
mv packages/api/tests/services/test_chat_service.py packages/api/tests/unit/services/test_chat_service.py
mv packages/api/tests/kg/test_graph_service.py packages/api/tests/unit/kg/test_graph_service.py
mv packages/api/tests/溯源/test_provenance.py packages/api/tests/unit/provenance/test_provenance.py
```

- [ ] **Step 4: Remove stale package files and path leftovers**

Delete no-longer-needed files if they become empty-only artifacts:

```bash
rm -f packages/api/tests/services/__init__.py
rm -f packages/api/tests/溯源/__init__.py
```

Also remove `__pycache__` directories if still present.

- [ ] **Step 5: Update markers and documentation to match physical structure**

Keep `pytestmark` aligned with directory intent:

- files under `contract/` use `pytest.mark.contract`
- files under `unit/` use `pytest.mark.unit`

Update `packages/api/tests/README.md` to describe the new physical paths, not the transitional layout.

- [ ] **Step 6: Update `pyproject.toml` test discovery assumptions if needed**

Ensure `packages/api/pyproject.toml` still works with the new layout and keeps:

```toml
testpaths = ["tests"]
markers = [
  "unit: ...",
  "contract: ...",
  "integration: ...",
]
```

- [ ] **Step 7: Run the fast backend suite**

Run:

```bash
./scripts/test_api.sh
```

Expected:

- PASS
- tests execute from `unit/` and `contract/` only

- [ ] **Step 8: Commit**

```bash
git add packages/api/tests packages/api/pyproject.toml
git commit -m "test(api): migrate backend tests into explicit layers"
```

## Task 3: Add Minimal Real Integration Coverage

**Files:**
- Create: `packages/api/tests/integration/conftest.py`
- Create: `packages/api/tests/integration/test_graph_search_smoke.py`
- Create: `packages/api/tests/integration/test_verification_sync_smoke.py`
- Modify: `scripts/test_integration.sh`
- Test: `./scripts/test_integration.sh`

- [ ] **Step 1: Write the first failing integration test for graph search**

Create `packages/api/tests/integration/test_graph_search_smoke.py`:

```python
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_graph_search_returns_demo_herb(client: AsyncClient):
    response = await client.get("/api/v1/graph/search", params={"q": "人参"})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(item["node"]["name"] == "人参" for item in data["items"])
```

- [ ] **Step 2: Write the second failing integration test for verification sync**

Create `packages/api/tests/integration/test_verification_sync_smoke.py`:

```python
import pytest

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_verify_endpoint_syncs_graph_node(client):
    create_response = await client.post(
        "/api/v1/verifications/",
        json={
            "entity_type": "herb",
            "entity_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2",
            "claimed_value": "黄芪补气固表。",
            "field_name": "description",
        },
    )
    verification_id = create_response.json()["id"]

    verify_response = await client.post(
        f"/api/v1/verifications/{verification_id}/verify",
        params={"status": "verified", "verdict": "integration pass"},
    )

    assert verify_response.status_code == 200
    node_response = await client.get("/api/v1/graph/node/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa2")
    assert node_response.status_code == 200
    assert node_response.json()["verification_id"] == verification_id
```

- [ ] **Step 3: Build a real integration fixture**

Create `packages/api/tests/integration/conftest.py` to:

- load the FastAPI app
- connect to real local services from `packages/api/.env`
- seed demo data before tests
- provide an `httpx.AsyncClient`

Recommended skeleton:

```python
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture(scope="session", autouse=True)
async def seed_demo_environment():
    ...


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 4: Make integration self-documenting**

In the fixture, fail early with a helpful message if required services are unavailable:

```python
raise RuntimeError("Integration tests require local PostgreSQL/Neo4j/Redis and seeded demo data")
```

Use explicit checks instead of obscure connection failures.

- [ ] **Step 5: Run the integration suite and make it pass**

Run:

```bash
./scripts/test_integration.sh
```

Expected:

- both smoke tests PASS

- [ ] **Step 6: Commit**

```bash
git add packages/api/tests/integration scripts/test_integration.sh
git commit -m "test(api): add real integration smoke coverage"
```

## Task 4: Harden Frontend Test Coverage Around Critical Routes

**Files:**
- Modify: `packages/web/src/test/setup.ts`
- Modify: `packages/web/src/test/render-with-providers.tsx`
- Create or modify: `packages/web/src/pages/GraphPage.test.tsx`
- Create or modify: `packages/web/src/App.test.tsx`
- Test: `pnpm --dir packages/web test --run`

- [ ] **Step 1: Write the failing graph page test**

Create `packages/web/src/pages/GraphPage.test.tsx`:

```tsx
import { screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

import GraphPage from './GraphPage'
import { graphApi } from '../services/api'

it('renders graph details for a routed herb page', async () => {
  vi.spyOn(graphApi, 'getHerbGraph').mockResolvedValue({
    center: { id: 'herb-1', name: '人参', status: 'verified', labels: ['Herb'] },
    nodes: [{ id: 'herb-1', name: '人参', status: 'verified', labels: ['Herb'] }],
    edges: [],
  })

  render(
    <MemoryRouter initialEntries={['/graph/人参']}>
      <Routes>
        <Route path="/graph/:name" element={<GraphPage />} />
      </Routes>
    </MemoryRouter>
  )

  expect(await screen.findByText(/人参 的知识图谱/)).toBeInTheDocument()
})
```

- [ ] **Step 2: Write the failing app-level route smoke**

Create `packages/web/src/App.test.tsx`:

```tsx
import { screen } from '@testing-library/react'

import App from './App'
import { renderWithProviders } from './test/render-with-providers'

it('renders top-level navigation and home route', () => {
  renderWithProviders(<App />)
  expect(screen.getByText('欢迎使用白草药坛')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: '知识搜索' })).toBeInTheDocument()
})
```

- [ ] **Step 3: Stabilize any remaining jsdom friction**

If the new tests expose more Ant Design jsdom issues, confine fixes to:

- `packages/web/src/test/setup.ts`
- shared render helpers

Do not pollute production code solely for test environment quirks.

- [ ] **Step 4: Run the frontend suite**

Run:

```bash
pnpm --dir packages/web test --run
pnpm --dir packages/web build
```

Expected:

- all frontend tests PASS
- production build still PASS

- [ ] **Step 5: Commit**

```bash
git add packages/web/src/pages/*.test.tsx packages/web/src/test packages/web/package.json packages/web/vite.config.ts packages/web/tsconfig.json
git commit -m "test(web): expand route and page coverage"
```

## Task 5: Add GitHub Actions Fast Gate

**Files:**
- Create: `.github/workflows/ci-fast.yml`
- Test: validate workflow syntax locally by inspection and by matching existing root commands

- [ ] **Step 1: Write the workflow file**

Create `.github/workflows/ci-fast.yml`:

```yaml
name: ci-fast

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  api-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      - name: Run API fast suite
        run: ./scripts/test_api.sh

  web-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - uses: pnpm/action-setup@v4
        with:
          version: 10.28.1
      - name: Install workspace deps
        run: pnpm install --frozen-lockfile
      - name: Run web tests
        run: pnpm run test:web
      - name: Build web
        run: pnpm --dir packages/web build
```

- [ ] **Step 2: Match the workflow to root command truth**

Before considering the workflow done, verify it only calls canonical commands or the direct install command needed before them.

The workflow must not introduce a second validation vocabulary.

- [ ] **Step 3: Sanity-check the fast gate against spec**

Verify by reading the file that:

- no PostgreSQL service is started
- no Neo4j service is started
- no E2E is run here
- it remains the fast gate only

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci-fast.yml
git commit -m "ci: add fast validation workflow"
```

## Task 6: Add GitHub Actions E2E Smoke Gate

**Files:**
- Create: `.github/workflows/ci-e2e.yml`
- Modify if needed: `scripts/test_e2e.sh`
- Test: `./scripts/test_e2e.sh`

- [ ] **Step 1: Write the E2E workflow**

Create `.github/workflows/ci-e2e.yml`:

```yaml
name: ci-e2e

on:
  pull_request:

jobs:
  e2e-smoke:
    runs-on: ubuntu-latest
    env:
      CI: "true"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: astral-sh/setup-uv@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - uses: pnpm/action-setup@v4
        with:
          version: 10.28.1
      - name: Install workspace deps
        run: pnpm install --frozen-lockfile
      - name: Run E2E smoke
        run: ./scripts/test_e2e.sh
```

- [ ] **Step 2: Make sure CI E2E does not depend on tmux**

If `scripts/test_e2e.sh` still shells into tmux during `CI=true`, stop and fix that before proceeding.

- [ ] **Step 3: Verify the smoke test remains intentionally minimal**

Ensure `tests/e2e/mainline.spec.ts` covers:

- home
- search
- graph
- chat
- verification

Do not expand to a large page matrix in this task.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/ci-e2e.yml scripts/test_e2e.sh tests/e2e/mainline.spec.ts playwright.config.ts
git commit -m "ci: add required e2e smoke workflow"
```

## Task 7: Synchronize Documentation And Merge Rules

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/acceptance/README.md`
- Modify: `docs/acceptance/graph-query-mainline.md`
- Modify: `docs/acceptance/chat-mainline.md`
- Modify: `docs/acceptance/verification-workflow.md`

- [ ] **Step 1: Update README command surface if any root command changed**

Keep `README.md` aligned with:

- `pnpm run demo`
- `pnpm run test:api`
- `pnpm run test:integration`
- `pnpm run test:web`
- `pnpm run test:e2e`
- `pnpm run verify`
- `pnpm run verify:full`

- [ ] **Step 2: Update docs to reference the migrated backend layout**

Adjust any references that still assume legacy backend directories like:

- `packages/api/tests/api/`
- `packages/api/tests/kg/`
- `packages/api/tests/services/`
- `packages/api/tests/溯源/`

- [ ] **Step 3: Add explicit required-check guidance**

Document in README or an adjacent CI section that the required GitHub checks are:

- `ci-fast / api-tests`
- `ci-fast / web-tests`
- `ci-e2e / e2e-smoke`

- [ ] **Step 4: Re-run full validation**

Run:

```bash
pnpm run verify:full
```

Expected:

- API PASS
- Web PASS
- E2E PASS

- [ ] **Step 5: Commit**

```bash
git add README.md docs/README.md docs/acceptance/README.md docs/acceptance/*.md
git commit -m "docs: align acceptance and ci documentation"
```

## Final Verification Checklist

- [ ] `./scripts/test_api.sh` passes with only `unit + contract`
- [ ] `./scripts/test_integration.sh` passes locally
- [ ] `pnpm --dir packages/web test --run` passes
- [ ] `pnpm --dir packages/web build` passes
- [ ] `./scripts/test_e2e.sh` passes locally
- [ ] `.github/workflows/ci-fast.yml` exists
- [ ] `.github/workflows/ci-e2e.yml` exists
- [ ] backend tests are physically migrated to `unit / contract / integration`
- [ ] acceptance docs still match the canonical root commands
