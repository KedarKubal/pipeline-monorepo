# Adobe Analytics Implementation — Northline Goods (Portfolio Project)

An end-to-end analytics implementation and reporting exercise for a fictional
outdoor-gear e-commerce site, built to demonstrate the full measurement
lifecycle: **plan → implement → validate → govern → report.**

## Why this exists

Most analytics portfolio pieces show a tag on a page. This one tries to show
the whole job: a tracking plan that a stakeholder could review, a data layer
an engineer could implement against, Launch rules that map 1:1 back to that
plan, server-side governance (processing rules + classifications), and a
reporting script that turns raw event counters into a funnel a marketer would
actually read.

**No live Adobe Analytics report suite or Launch property exists for this
project.** Everything that would normally be configured in Adobe's UI (report
suite variable setup, Launch library publish, processing rules, SAINT
classification uploads) is documented here as if it had been — see the "What's
simulated" section below for the honest boundary.

## Structure

```
tracking-plan/
  tracking-plan.md          Full spec: events, eVars, props, products string, page map
  tracking-plan.xlsx        Same spec as a stakeholder-facing workbook
  build_tracking_plan.py    Script that generates the .xlsx from this README's source of truth

demo-site/
  index.html, plp.html, pdp.html, cart.html,
  checkout.html, confirmation.html, 404.html
  js/datalayer.js           window.digitalData contract + mock Launch/_satellite adapter
  js/products-data.js       Static product catalog
  js/app.js                 Cart state, shared header/footer, UI wiring
  css/style.css             Site styling

launch-rules/                Exported rule JSON (data-element-mapped, mirrors tracking-plan.md)

processing-rules-classifications/
  processing-rules.md                  Server-side hit cleanup rules + rationale
  classification-product-sku.csv       SAINT classification file, Product SKU
  classification-marketing-channel.csv SAINT classification file, Marketing Channel (eVar13)

reporting/
  adobe_analytics_report.py  Adobe Analytics 2.0 API client + mock-mode fallback
  sample_response.json       Mock API response, real /reports schema
  requirements.txt
```

## How the pieces connect

1. **`tracking-plan.md`/`.xlsx`** is the source of truth. Every eVar, prop,
   and success event number here is referenced by name in every other folder
   — nothing downstream invents a new variable.
2. **`demo-site/js/datalayer.js`** implements that plan as code: a page-load
   `digitalData` object plus `_satellite.track()` calls for interaction
   events, exactly the contract a real Launch property would bind to.
3. **`launch-rules/*.json`** are what you'd export from Launch after building
   rules against that data layer — Library Loaded for page views, Direct Call
   rules for everything interaction-based (add to cart, checkout steps, promo
   codes, purchase).
4. **`processing-rules-classifications/`** covers the two things that live in
   Adobe's Admin Console rather than in Launch: data cleanup that runs on
   every hit (processing rules) and enrichment that's imported on a schedule
   (SAINT classifications for Product SKU and Marketing Channel).
5. **`reporting/adobe_analytics_report.py`** hits the real Adobe Analytics 2.0
   Reporting API when credentials are present, and falls back to a
   schema-accurate mock response otherwise — it pulls Product Views → Adds to
   Cart → Purchases by SKU and computes funnel-conversion rates.

## Running the demo site

It's static HTML/JS/CSS — no build step:

```bash
cd demo-site
python3 -m http.server 8000
# open http://localhost:8000
```

Click through Home → a category → a product → add to cart → checkout →
confirmation, then open the **AEP Debugger (mock)** drawer at the bottom of
the screen. It's a stand-in for the real Adobe Experience Platform Debugger
extension: every beacon (page view or direct call), the variables it set, and
the live `window.digitalData` object are all visible in real time.

## Running the reporting script

```bash
cd reporting
pip install -r requirements.txt
python3 adobe_analytics_report.py --mock
```

Drop `--mock` and set `ADOBE_CLIENT_ID`, `ADOBE_CLIENT_SECRET`, `ADOBE_ORG_ID`,
`ADOBE_GLOBAL_COMPANY_ID` (a Server-to-Server OAuth credential from Adobe
Developer Console) to run it against a real report suite — the request/parsing
logic doesn't change, only where the response comes from.

## What's simulated vs. real

| Piece | Status |
|---|---|
| Tracking plan | Real spec, written as if for an actual net-new implementation |
| Data layer (`digitalData`) | Real, runnable JavaScript |
| Demo site | Real, runnable — deployable as-is |
| Launch rules | Real rule *logic and structure*; JSON shaped like a Launch export, but not pulled from an actual Launch property (none exists) |
| Processing rules / classifications | Documented as specs — these are Admin Console configuration, not files |
| Reporting script | Real API client code; run in `--mock` mode against a schema-accurate sample response, since no live report suite exists |

## Known gaps (called out deliberately, not hidden)

- No consent/CMP gating — a production build would block eVar/event capture
  (particularly `event2`/cart data) pre-consent.
- No cross-device or Customer Attributes / CJA integration.
- Processing rules and classifications are specified, not testable, since
  they require a live report suite to execute against.
