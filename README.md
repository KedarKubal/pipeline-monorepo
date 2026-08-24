# Config Toggle Service

[![Node.js](https://img.shields.io/badge/Node.js-20-339933?style=for-the-badge&logo=node.js)](https://nodejs.org)
[![Express](https://img.shields.io/badge/Express-4-black?style=for-the-badge&logo=express)](https://expressjs.com)
[![Jest](https://img.shields.io/badge/Tested_with-Jest-C21325?style=for-the-badge&logo=jest)](https://jestjs.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com)

A small, production-shaped Node.js/Express microservice for managing **feature flags and runtime config toggles**, built around clean-code fundamentals: layered architecture, centralized error handling, input validation, and dependency-light file persistence — no database required to run it.

---

## Why This Project

Most "feature flag" tutorials either pull in a full SaaS platform or a database you don't need for a small team. This project is the deliberately minimal middle ground: a self-contained service you can drop into a side project or internal tool, read end-to-end in one sitting, and trust because every code path is covered by tests.

It doubles as a **Node.js clean-code reference** — the "cleanup" half of the brief — demonstrating:
- Layered architecture (routes → controllers → services), each with one job
- No stray `process.env` reads outside a single config module
- Centralized, typed error handling instead of scattered try/catch status codes
- Concurrency-safe file writes (a real gotcha with flat-file persistence)
- ESLint + Prettier enforced, zero warnings
- Full Jest + Supertest coverage (unit + integration)

It's also the **control plane for the wider `platform-monorepo`** — its audit
trail is consumed by `migration-platform`'s ETL pipeline, and its flags are
read at runtime by `migration-platform`'s CLI, the Adobe Analytics demo site,
and a Flutter Widgetbook catalog. See the [root README](../../README.md) for
the full cross-project picture.

---

## Project Journey

### Phase 1 — Project Scaffolding

Laid out a layered structure so each concern lives in exactly one place:

```
src/
├── config/       # env vars read here, and ONLY here
├── controllers/  # thin HTTP handlers
├── services/     # business logic + persistence
├── routes/       # Express routers
├── middleware/   # auth, validation, error handling
├── utils/        # logger, AppError
└── data/         # flags.json (file-backed store)
```

### Phase 2 — Core Toggle Engine (`src/services/flags.service.js`)

The heart of the service. Flags are stored as flat JSON with a strict schema:

```json
{
  "key": "dark-mode",
  "description": "Enables dark theme across the web dashboard.",
  "enabled": true,
  "environments": ["development", "staging", "production"],
  "updatedBy": "seed",
  "updatedAt": "2026-01-15T09:00:00.000Z"
}
```

**Problem solved:** flat files aren't transaction-safe. Two concurrent writes can interleave and corrupt the file. Fixed with:
- A promise-chained **write queue** — every write waits for the previous one to finish
- **Write-to-temp-then-rename** — never leaves a half-written file on disk, even on crash

### Phase 3 — REST API (`src/routes/`, `src/controllers/`)

| Endpoint | Auth | Description |
|---|---|---|
| `GET /api/health` | none | Liveness check for containers/orchestration |
| `GET /api/flags` | none | List all flags (optional `?environment=` filter) |
| `GET /api/flags/:key` | none | Get a single flag |
| `POST /api/flags` | API key | Create a new flag |
| `PATCH /api/flags/:key` | API key | Update description / enabled / environments |
| `POST /api/flags/:key/toggle` | API key | Flip `enabled` true ↔ false |
| `DELETE /api/flags/:key` | API key | Remove a flag |
| `GET /api/flags/:key/history` | none | Full audit history for one flag |
| `GET /api/flags/audit` | none | All audit entries, optional `?since=<ISO timestamp>` filter |

Reads are public (so dashboards/consumers can poll freely); writes require an `X-API-Key` header.

Note: `GET /api/flags/audit` is registered *before* `GET /api/flags/:key` in
the router, so the literal string `"audit"` isn't matched as a flag key.

### Phase 4 — Validation & Auth (`src/middleware/`)

- `validateFlagPayload.js` — rejects malformed bodies before they reach business logic (wrong types, missing required fields)
- `apiKeyAuth.js` — simple, swappable API-key gate on all write routes
- `errorHandler.js` — every error in the app (validation, not-found, conflict, unexpected) resolves to one consistent JSON error shape:

```json
{ "error": { "message": "Flag \"x\" not found.", "code": "NOT_FOUND" } }
```

### Phase 5 — Toggle Dashboard (`public/dashboard.html`)

A single static HTML page — no build step, no framework — served at `/dashboard`, showing every flag with a live toggle switch. Enter an API key to flip flags directly from the browser.

### Phase 6 — Testing (`tests/`)

17 tests, unit + integration, all green:

```
tests/flags.service.test.js   — business logic, validation, concurrency safety
tests/flags.routes.test.js    — full HTTP surface via Supertest (incl. auth + 404s)
```

```
npm test
```

### Phase 7 — Containerization (`Dockerfile`, `docker-compose.yml`)

- Multi-stage `Dockerfile`: install stage → minimal Alpine runtime, **non-root user**, built-in `HEALTHCHECK`
- `docker-compose.yml`: one command to run it, with a named volume so flag state survives container restarts

```
docker compose up --build
```

### Phase 8 — Code Quality Tooling

- ESLint (`eslint:recommended` + Prettier integration) — zero warnings on `npm run lint`
- Prettier for consistent formatting
- `.env.example` documents every config knob; `.env` is git-ignored

### Phase 9 — Audit Log (`src/services/flags.service.js`, `src/routes/`)

Every create/update/toggle/delete now appends an entry to a new
`src/data/flag_audit.json` — `{key, action, previousState, newState,
timestamp}` — reusing the same write-queue + atomic-rename pattern as
`flags.json`, rather than reinventing persistence for it.

`appendAuditEntry` is intentionally **not** wrapped in its own `serialize()`
call: every caller is already inside a serialized mutation, and
double-wrapping would deadlock the write queue.

Two new read endpoints expose it: `GET /api/flags/:key/history` for a single
flag's history, and `GET /api/flags/audit?since=<ISO timestamp>` for the full
log — the latter is what `migration-platform`'s `FlagAuditExtractor` polls to
ingest flag changes as a first-class ETL source.

---

## Running Locally

### Prerequisites

- Node.js 18+ (repo tested on Node 20/22)

### Steps

```bash
# 1. Clone and install
git clone <this-repo-url>
cd config-toggle-service
npm install

# 2. Configure environment
cp .env.example .env
# edit .env if you want a custom API key

# 3. Run
npm start
# or, with auto-reload during development:
npm run dev

# 4. Try it
curl http://localhost:3000/api/flags
curl -X POST http://localhost:3000/api/flags/dark-mode/toggle \
  -H "X-API-Key: dev-local-key"

# 5. Open the dashboard
open http://localhost:3000/dashboard/dashboard.html
```

### Running with Docker

```bash
docker compose up --build
# service available at http://localhost:3000
```

### Running Tests

```bash
npm test          # full suite, unit + integration
npm run test:watch
npm run lint       # ESLint
npm run format     # Prettier write
```

---

## API Reference

### List flags
```
GET /api/flags
GET /api/flags?environment=production
```

### Get one flag
```
GET /api/flags/:key
```

### Create a flag *(requires `X-API-Key`)*
```
POST /api/flags
Content-Type: application/json

{
  "key": "new-search-ui",
  "description": "Rolls out the redesigned search experience.",
  "enabled": false,
  "environments": ["development"]
}
```

### Update a flag *(requires `X-API-Key`)*
```
PATCH /api/flags/:key
Content-Type: application/json

{ "enabled": true }
```

### Toggle a flag *(requires `X-API-Key`)*
```
POST /api/flags/:key/toggle
```

### Delete a flag *(requires `X-API-Key`)*
```
DELETE /api/flags/:key
```

### Get audit history for a flag
```
GET /api/flags/:key/history
```

### Get all audit entries
```
GET /api/flags/audit
GET /api/flags/audit?since=2026-08-01T00:00:00.000Z
```

Every create/update/toggle/delete appends an entry to
`src/data/flag_audit.json` (same write-queue + atomic temp-file-then-rename
pattern as `flags.json`). This is what `migration-platform`'s
`FlagAuditExtractor` polls to ingest flag changes as a first-class ETL
source — see the [root README](../../README.md) for the full cross-project
picture.

**Flag key format:** lowercase, alphanumeric, hyphen-separated — e.g. `new-checkout-flow`.
**Supported environments:** `development`, `staging`, `production`.

---

## Project Structure

```
config-toggle-service/
│
├── src/
│   ├── config/index.js              # ALL env var reads happen here
│   ├── controllers/flags.controller.js
│   ├── services/flags.service.js    # CRUD + concurrency-safe persistence
│   ├── routes/
│   │   ├── flags.routes.js
│   │   └── health.routes.js
│   ├── middleware/
│   │   ├── apiKeyAuth.js
│   │   ├── errorHandler.js
│   │   └── validateFlagPayload.js
│   ├── utils/
│   │   ├── AppError.js
│   │   └── logger.js
│   ├── data/
│   │   ├── flags.json               # seeded sample flag data
│   │   └── flag_audit.json          # append-only audit log
│   └── app.js                       # Express app assembly
│
├── public/
│   └── dashboard.html               # toggle UI, no build step
│
├── tests/
│   ├── flags.service.test.js
│   └── flags.routes.test.js
│
├── server.js                        # entry point, graceful shutdown
├── Dockerfile                       # multi-stage, non-root, healthcheck
├── docker-compose.yml
├── .env.example
├── .eslintrc.json
├── .prettierrc
└── package.json
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `NODE_ENV` | `development` / `production` | `development` |
| `PORT` | HTTP port | `3000` |
| `API_KEYS` | Comma-separated keys allowed to write | `dev-local-key` |
| `CORS_ORIGIN` | Allowed CORS origin | `*` |
| `DATA_FILE_PATH` | Path to the flag store JSON file | `src/data/flags.json` |

---

## Design Decisions & Trade-offs

- **File-backed store instead of a database** — deliberate, given "small and easy" scope. The write-queue + atomic-rename pattern makes it safe for low/moderate write volume; a real DB (Postgres/Redis) is a drop-in swap in `flags.service.js` if traffic grows.
- **API-key auth instead of JWT/OAuth** — appropriate for an internal tool; the auth middleware is isolated so swapping in a heavier scheme touches one file.
- **No frontend framework for the dashboard** — a single static HTML file keeps the "small and easy" promise; reaches for React only if the UI grows real complexity.

## Possible Extensions

- Percentage-based rollouts (`rolloutPercentage` field + consistent hashing on a user ID)
- Swap file store for Postgres/Redis behind the same service interface
- Kubernetes manifests (`namespace.yaml`, `deployment.yaml`, `service.yaml`) — straightforward given the existing Dockerfile

---

## License

MIT
