# Migration Platform

An ETL pipeline that migrates legacy customer/order data (CSV + legacy relational DB)
into a normalized target schema, with validation, quarantine, and transactional
batch loading. It also ingests the audit trail from the platform's
[Config Toggle Service](../../services/config-toggle-service/README.md) as a
second, structurally different data source, and reads a live flag at runtime
to gate one of its own validation rules — see
[Coupling with config-toggle-service](#coupling-with-config-toggle-service)
below.

## Data flow

```
                 EXTRACT                    TRANSFORM                      LOAD
            ┌───────────────┐         ┌──────────────────┐         ┌──────────────────┐
customers   │ CSV Reader     │ raw df  │ clean: split name │ valid  │ upsert Customer   │
_legacy.csv │──────────────> │────────>│ normalize email/  │ rows   │ upsert Address    │
            │                │         │ phone, dates      │───────>│ (ON CONFLICT DO   │
            └───────────────┘         │ validate:          │        │  UPDATE, batched) │
                                       │  - email format    │        └──────────────────┘
orders_     ┌───────────────┐         │  - dedup by email  │                 │
legacy      │ Legacy DB      │ raw df  │  - FK to customer  │ valid  ┌──────────────────┐
(table)     │ Reader         │────────>│  - qty/price sane  │ rows   │ upsert Product    │
            │──────────────> │         │──────────────────>│───────>│ upsert Order      │
            └───────────────┘         └──────────────────┘         │ upsert OrderItem  │
                                              │                      └──────────────────┘
                                              │ invalid rows
                                              ▼
                                    ┌────────────────────┐
                                    │ Quarantine          │
                                    │ (DataFrame +        │
                                    │  rejection_reason)  │
                                    └────────────────────┘

flag_audit  ┌────────────────────┐ raw df  ┌────────────────────┐ valid  ┌──────────────────┐
(toggle svc)│ FlagAuditExtractor  │────────>│ transform_flag_audit│ rows  │ upsert            │
            │ GET /api/flags/     │         │ validate action /  │───────>│ FlagChangeAudit   │
            │ audit?since=...     │         │ changed_at         │        │ (natural key:     │
            └────────────────────┘         └────────────────────┘        │ flag_key+changed_at)│
                                                                          └──────────────────┘
```

**Target schema** (normalized from a flat legacy export):

```
customers ──1:N── addresses
customers ──1:N── orders ──1:N── order_items ──N:1── products
```

`FlagChangeAudit` has no FK dependents, so it loads independently of the
customer/order chain above — it can run anywhere after customers in the
dependency-ordered load sequence.

## Project layout

```
src/
  config.py           Environment-driven settings, fails fast on missing config
  models/
    base.py            SQLAlchemy declarative base + timestamp mixin
    target.py           Target schema: Customer, Address, Product, Order, OrderItem,
                        FlagChangeAudit
  extract/
    base.py             Extractor ABC + column-validation helper
    csv_reader.py        CustomerCsvExtractor (legacy customers CSV)
    legacy_db_reader.py  LegacyOrdersDbExtractor (legacy orders_legacy table)
    flag_audit_reader.py  FlagAuditExtractor (config-toggle-service audit log,
                          fails loud on a bad fetch — see below)
  transform/
    cleaners.py          Pure functions: name split, email/phone normalize, type
                         coercion. coerce_timestamps preserves full datetime
                         precision for audit entries (coerce_dates truncates to
                         date-only and would collapse same-day audit events)
    validators.py         Row-level validation -> ValidationResult(valid, quarantined)
    pipeline.py            Wires cleaners + validators into transform_customers /
                           transform_order_lines / transform_flag_audit
  load/
    loader.py            TargetLoader: batched, transactional ON CONFLICT DO UPDATE
                          upserts, in dependency order (customers -> addresses ->
                          products -> orders -> order_items -> flag_change_audits)
  orchestration/
    cli.py              Click CLI: `run` command wires extract -> transform -> load;
                        `--flags-audit-since <timestamp>` flag, defaulting to the
                        last successful run tracked in a small state file
    state.py            Tracks last-successful-run timestamp for incremental
                        flag-audit extraction
  flags_client.py        FlagsClient: reads a live flag from config-toggle-service
                         at runtime (fail-open) to gate a validation rule
migrations/              Alembic migrations for the target schema
tests/
  unit/                  Pure-function tests for cleaners + validators (no DB, no I/O),
                         plus FlagAuditExtractor and FlagsClient tests (mocked HTTP,
                         no live toggle-service required)
  integration/            End-to-end test against an in-memory SQLite DB
sample_data/              Demo CSV + SQL seed for the legacy orders table
```

## Design decisions worth knowing about

- **Quarantine, don't crash or silently drop.** Invalid rows (bad email, orphaned
  FK, non-positive quantity, etc.) are split into a `quarantined` DataFrame with a
  `rejection_reason` column instead of raising or vanishing. A migration run tells
  you exactly what it couldn't place.
- **Idempotent by design.** All loads use `INSERT ... ON CONFLICT DO UPDATE` keyed on
  natural/business keys (`legacy_id`, `sku`, `legacy_order_id`, `(order_id, product_id)`,
  `(flag_key, changed_at)` for audit entries). Re-running the pipeline on the same
  source is safe and just re-syncs.
- **Dependency-ordered, batched transactions.** Customers load before addresses/orders;
  products load before order_items — never leaves a child row pointing at a
  parent that doesn't exist yet. `LOAD_BATCH_SIZE` bounds transaction/memory size.
- **Pure transform functions.** Everything in `cleaners.py` is `DataFrame -> DataFrame`
  with no I/O, which is what makes the unit suite run in well under a second
  with no database required.
- **Two deliberately different failure philosophies for the two toggle-service
  integrations.** `FlagsClient` (runtime read, gating a validation rule) fails
  open — a flag-service outage should never crash a migration run. 
  `FlagAuditExtractor` (the ETL source) fails loud — silently skipping an audit
  batch would mean the pipeline reports success while quietly missing data,
  which is exactly what the quarantine philosophy above exists to prevent.

## Getting started

### 1. Local dev setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env   # edit DB URLs if needed
```

### 2. Run tests (no database required)

```bash
pytest -v
```

### 3. Spin up Postgres + apply migrations

```bash
docker compose up -d postgres
alembic upgrade head
```

Note: this project's `docker-compose.yml` maps Postgres to host port `5433`
(not the default `5432`), to avoid conflicting with a native host Postgres
process.

### 4. Run the migration

```bash
# Dry run first — extracts + transforms, reports quarantine stats, writes nothing
python -m src.orchestration.cli run \
  --customers-csv sample_data/customers_legacy.csv \
  --dry-run

# Then for real
python -m src.orchestration.cli run \
  --customers-csv sample_data/customers_legacy.csv

# Include the flag-audit source (requires config-toggle-service running,
# see ../../services/config-toggle-service)
python -m src.orchestration.cli run \
  --customers-csv sample_data/customers_legacy.csv \
  --flags-audit-since 2026-08-01T00:00:00Z
```

### 5. Or run everything via Docker

```bash
docker compose up --build
```

This starts Postgres (seeded with the demo `orders_legacy` table via
`sample_data/legacy_orders_seed.sql`) and runs the `app` container's migration
command against it.

## Coupling with config-toggle-service

This project talks to the platform's
[Config Toggle Service](../../services/config-toggle-service/README.md) in
two independent ways:

1. **`FlagAuditExtractor`** (`src/extract/flag_audit_reader.py`) polls
   `GET /api/flags/audit?since=<timestamp>`, treating the toggle service's
   audit trail as just another ETL source — proving the "add an `Extractor`
   subclass, nothing else changes" seam this pipeline is built around.
   Fails loud (raises `ExtractionError`) on timeout, connection failure, HTTP
   error, or an unexpected response shape, rather than silently skipping a
   batch.
2. **`FlagsClient`** (`src/flags_client.py`) reads a single flag at runtime
   to gate a stricter email-validation rule, caching for the duration of the
   run and failing open (`enabled: false`) if the service is unreachable — a
   missing flag service should never be able to crash a migration.

See the [root README](../../README.md) for how these fit into the platform's
full architecture, alongside the other two consumers (the Adobe Analytics
demo site and the Flutter Widgetbook catalog).

## Extending to a new source

Add a new `Extractor` subclass in `src/extract/` returning a DataFrame with the
columns your transform step expects — nothing in `transform/` or `load/` needs to
change. This is the seam the whole architecture is built around; `flag_audit_reader.py`
is a real example of using it for a source that isn't a flat file or a SQL table.

## Known limitations / next steps

- `order_date`/`signup_date` are stored as ISO date **strings** in the target schema
  for simplicity; a production version should use `sa.Date`.
- The legacy DB extractor assumes the legacy table is reachable via the same
  SQLAlchemy-supported dialect as the target DB — for a truly heterogeneous legacy
  source (e.g. mainframe export, proprietary format) you'd add a dedicated extractor.
- No retry/backoff on transient DB connection errors — worth adding
  (`tenacity` or similar) before a production cutover.
- Quarantined rows are only logged/returned in-process; for a real migration you'd
  want them written to a `quarantine` table or file for follow-up.
- `GET /:key/history` on pre-seeded flags returns an empty history by design —
  those flags were never written through the audited create/update/toggle
  path, so there's nothing in the audit log for them yet. Not a bug.
