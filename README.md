# Pipeline Monorepo

A linear, four-stage data pipeline built from four otherwise-independent
projects, demonstrating real cross-service data flow rather than four repos
sharing a `.git` folder.

Each stage's output is the next stage's input:

1. **`stages/01-adobe-analytics-demo`** — a static e-commerce demo site. Every
   `_satellite.track()` call (add-to-cart, purchase, ...) is also persisted
   to `demo-site/data/events.jsonl` by a small Node collector server.
2. **`stages/02-migration-platform`** — a Python ETL pipeline. Its
   `AnalyticsEventsExtractor` reads `events.jsonl`, validates rows
   (quarantining any with a missing event name or unparsable timestamp,
   per the project's existing quarantine-don't-crash philosophy), and
   aggregates the trailing 24h window into a `cart_abandonment_rate` metric,
   loaded into a `funnel_metrics` table.
3. **`stages/03-config-toggle-service`** — a Node/Express feature-flag
   service. migration-platform reads the latest metric and writes the
   `high-cart-abandonment-alert` flag on or off depending on whether the
   metric crosses a configurable threshold (default 0.7).
4. **`stages/04-flutter-dsm`** — a Flutter design-system + Widgetbook
   catalog. Its "Pipeline Insights" dashboard polls both the alert flag and
   a small read-only metrics API (also served by migration-platform) every
   5 seconds, rendering the current abandonment rate and alert state live.

## Why this shape

The four sub-projects were already independently solid (each with its own
test suite, its own README, its own reason to exist). The interesting
engineering problem wasn't building four things — it was making them
genuinely depend on each other's output, in one direction, with each stage's
Extractor/Transform/Load pattern reused where it fit and extended (not
copy-pasted) where it didn't.

## Running it locally

Four services, four terminals:

```bash
# Terminal 1 — flag service
cd stages/03-config-toggle-service && cp .env.example .env && npm install && npm start

# Terminal 2 — demo site (emits events)
cd stages/01-adobe-analytics-demo/demo-site && node server.js

# Terminal 3 — metrics API (read-only)
cd stages/02-migration-platform
cp .env.example .env   # fill in TARGET_DB_URL etc. — see .env.example
docker compose up -d postgres
alembic upgrade head
python -m src.orchestration.cli serve-metrics-api

# Terminal 4 — Widgetbook dashboard
cd stages/04-flutter-dsm/packages/dsm_widgetbook
flutter run -d chrome \
  --dart-define=TOGGLE_SERVICE_URL=http://localhost:3000 \
  --dart-define=METRICS_API_URL=http://localhost:8001
```

Then generate some traffic on the demo site (click through add-to-cart /
checkout, or `curl -X POST http://localhost:8000/api/events ...`) and run
the pipeline:

```bash
cd stages/02-migration-platform
python -m src.orchestration.cli run-funnel-metrics
python -m src.orchestration.cli sync-alert-flag
```

Watch the Widgetbook dashboard (Pipeline Insights → Cart Abandonment
Dashboard) update within ~5 seconds — no page refresh needed.

## Design decisions worth knowing about

- **Fail-open reads, fail-loud writes.** Every flag *read* in this pipeline
  (Flutter's `FlagService`, Python's `FlagsClient.is_enabled`) fails open —
  a down toggle-service should never crash a migration run or break the
  dashboard. But the flag *write* (`FlagsClient.set_enabled`, used by
  `sync-alert-flag`) fails loud, since there's no safe default for "did we
  successfully record this decision or not."
- **Server defaults the timestamp, not the client.** The demo-site
  collector fills in `timestamp` server-side if a caller omits it, rather
  than trusting every future caller to always send one — the extractor's
  strict validation is correct; the gap was making the server layer robust
  to callers that don't set it.
- **Metrics API is deliberately minimal.** `serve-metrics-api` is a single
  read-only endpoint built on Python's stdlib `http.server`, not a new
  framework dependency — consistent with the demo-site's collector server,
  which is also plain Node `http` rather than Express.

## Known gaps

- The metrics API and Postgres both need to be reachable from wherever
  Widgetbook runs (`localhost` by default) — a real deployment would need
  proper service discovery / env-based URLs, not hardcoded `--dart-define`s.
- No retry/backoff between pipeline stages — `run-funnel-metrics` and
  `sync-alert-flag` are run manually or via cron, not triggered by an event.
- Alembic migrations in `migration-platform` are hand-reviewed, not
  auto-applied on `docker compose up` — see that stage's own README for
  its migration history and design rationale.

## Individual stage documentation

Each stage keeps its own detailed README — worth reading for the parts of
this pipeline that predate the cross-stage coupling:

- [`stages/01-adobe-analytics-demo/README.md`](stages/01-adobe-analytics-demo/README.md)
- [`stages/02-migration-platform/README.md`](stages/02-migration-platform/README.md)
- [`stages/03-config-toggle-service/README.md`](stages/03-config-toggle-service/README.md)
- [`stages/04-flutter-dsm/README.md`](stages/04-flutter-dsm/README.md)
