# Migration Platform

An ETL pipeline that migrates legacy customer/order data (CSV + legacy relational DB)
into a normalized target schema, with validation, quarantine, and transactional
batch loading.

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
```

**Target schema** (normalized from a flat legacy export):

```
customers ──1:N── addresses
customers ──1:N── orders ──1:N── order_items ──N:1── products
```

## Project layout

```
src/
  config.py           Environment-driven settings, fails fast on missing config
  models/
    base.py            SQLAlchemy declarative base + timestamp mixin
    target.py           Target schema: Customer, Address, Product, Order, OrderItem
  extract/
    base.py             Extractor ABC + column-validation helper
    csv_reader.py        CustomerCsvExtractor (legacy customers CSV)
    legacy_db_reader.py  LegacyOrdersDbExtractor (legacy orders_legacy table)
  transform/
    cleaners.py          Pure functions: name split, email/phone normalize, type coercion
    validators.py         Row-level validation -> ValidationResult(valid, quarantined)
    pipeline.py            Wires cleaners + validators into transform_customers /
                           transform_order_lines
  load/
    loader.py            TargetLoader: batched, transactional ON CONFLICT DO UPDATE
                          upserts, in dependency order (customers -> addresses ->
                          products -> orders -> order_items)
  orchestration/
    cli.py              Click CLI: `run` command wires extract -> transform -> load
migrations/              Alembic migrations for the target schema
tests/
  unit/                  Pure-function tests for cleaners + validators (no DB, no I/O)
  integration/            End-to-end test against an in-memory SQLite DB
sample_data/              Demo CSV + SQL seed for the legacy orders table
```

## Design decisions worth knowing about

- **Quarantine, don't crash or silently drop.** Invalid rows (bad email, orphaned
  FK, non-positive quantity, etc.) are split into a `quarantined` DataFrame with a
  `rejection_reason` column instead of raising or vanishing. A migration run tells
  you exactly what it couldn't place.
- **Idempotent by design.** All loads use `INSERT ... ON CONFLICT DO UPDATE` keyed on
  natural/business keys (`legacy_id`, `sku`, `legacy_order_id`, `(order_id, product_id)`).
  Re-running the pipeline on the same source is safe and just re-syncs.
- **Dependency-ordered, batched transactions.** Customers load before addresses/orders;
  products load before order_items — never leaves a child row pointing at a
  parent that doesn't exist yet. `LOAD_BATCH_SIZE` bounds transaction/memory size.
- **Pure transform functions.** Everything in `cleaners.py` is `DataFrame -> DataFrame`
  with no I/O, which is what makes the 19-test unit suite run in well under a second
  with no database required.

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

### 4. Run the migration

```bash
# Dry run first — extracts + transforms, reports quarantine stats, writes nothing
python -m src.orchestration.cli run \
  --customers-csv sample_data/customers_legacy.csv \
  --dry-run

# Then for real
python -m src.orchestration.cli run \
  --customers-csv sample_data/customers_legacy.csv
```

### 5. Or run everything via Docker

```bash
docker compose up --build
```

This starts Postgres (seeded with the demo `orders_legacy` table via
`sample_data/legacy_orders_seed.sql`) and runs the `app` container's migration
command against it.

## Extending to a new source

Add a new `Extractor` subclass in `src/extract/` returning a DataFrame with the
columns your transform step expects — nothing in `transform/` or `load/` needs to
change. This is the seam the whole architecture is built around.

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
