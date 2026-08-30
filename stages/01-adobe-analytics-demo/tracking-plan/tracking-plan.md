# Tracking Plan — "Northline Goods" Demo E-Commerce Site

**Scope:** Adobe Analytics implementation via Adobe Launch, AppMeasurement-based data layer.
**Site flow:** Home → PLP (category/search results) → PDP → Cart → Checkout (3 steps) → Order Confirmation
**Report Suite (hypothetical):** `northlinegoods-prod` (prod), `northlinegoods-dev` (dev/QA)

---

## 1. Naming & Governance Conventions

- Data layer object: `window.digitalData` (Adobe-style, page-load object), updated via `_satellite.track()` calls for post-load interactions.
- All custom event names are `snake_case` and namespaced by area: `product.*`, `cart.*`, `checkout.*`, `search.*`, `promo.*`.
- Launch rule naming: `[Area] Trigger — Action` (e.g., `Cart — Click — Add to Cart`).
- eVars/props are numbered in the order they were adopted, not grouped by topic — mirrors how a real report suite evolves over time and avoids renumbering churn.

---

## 2. Success Events (Metrics)

| # | Event Name | Type | Fires On | Serialization | Notes |
|---|---|---|---|---|---|
| event1 | Product View | Counter | PDP load | Page load | Fires once per PDP view |
| event2 | Add to Cart | Counter | "Add to Cart" click | Link tracking (`s.tl`) | Linked to product string |
| event3 | Remove from Cart | Counter | "Remove" click on cart page | Link tracking | Linked to product string |
| event4 | Checkout Initiated | Counter | "Checkout" click from cart | Link tracking | Cart → checkout entry |
| event5 | Checkout Step Complete | Counter | "Continue" click on each checkout step | Link tracking | Use eVar9 to differentiate step |
| event6 | Promo Code Applied — Success | Counter | Valid promo code submitted | Link tracking | |
| event7 | Promo Code Applied — Failure | Counter | Invalid promo code submitted | Link tracking | |
| event8 | Internal Search Performed | Counter | Search submitted | Link tracking | Paired with eVar6/eVar7 |
| event9 | Purchase | Counter | Order confirmation page load | Page load | Should equal Orders |
| purchase (product-string) | Revenue / Units | Currency / Counter | Order confirmation page load | Page load, in `s.products` string | Standard Orders + Revenue + Units metrics |

---

## 3. eVars

| # | Name | Description | Value Example | Allocation | Expiration | Data Layer Source |
|---|---|---|---|---|---|---|
| eVar1 | Page Name | Canonical page/template name | `PDP: Trail Runner Jacket` | Most Recent | Visit | `digitalData.page.pageName` |
| eVar2 | Site Section | Top-level nav section | `Outerwear` | Most Recent | Visit | `digitalData.page.section` |
| eVar3 | Product Name | Product viewed/acted on | `Trail Runner Jacket` | Most Recent | Visit | `digitalData.product[0].name` |
| eVar4 | Product SKU | Unique product identifier | `NLG-JCK-1042` | Most Recent | Visit | `digitalData.product[0].sku` |
| eVar5 | Product Category | Product's category/subcategory | `Outerwear/Jackets` | Most Recent | Visit | `digitalData.product[0].category` |
| eVar6 | Internal Search Term | Raw search query, lowercased | `waterproof jacket` | Most Recent | Visit | `digitalData.search.term` |
| eVar7 | Internal Search Results Count | # results returned | `14` | Most Recent | Event ("hit") | `digitalData.search.resultsCount` |
| eVar8 | Cart ID | Session-scoped cart identifier | `cart_8f3ac1` | Most Recent | Visit | `digitalData.cart.id` |
| eVar9 | Checkout Step Name | Current checkout step | `shipping` \| `payment` \| `review` | Most Recent | Event ("hit") | `digitalData.checkout.stepName` |
| eVar10 | Order ID | Completed order identifier | `NLG-100234` | Most Recent | Event ("hit") | `digitalData.order.orderId` |
| eVar11 | Promo Code | Promo code entered | `WELCOME10` | Most Recent | Event ("hit") | `digitalData.promo.code` |
| eVar12 | PLP Sort/Filter Selection | Active sort or filter facet | `sort:price_asc` | Most Recent | Event ("hit") | `digitalData.plp.activeFilter` |
| eVar13 | Marketing Channel | Derived from `utm_source`/`utm_medium` | `paid_social` | Original Value | Visit | Query param parsed on landing |
| eVar14 | Visitor Type | New vs. returning (first-party cookie check) | `new` \| `returning` | Most Recent | Visit | Set in Launch rule via cookie |
| eVar15 | Error Flag | Marks 404/error pages | `404` | Most Recent | Event ("hit") | `digitalData.page.errorCode` |

## 4. Props (pathing-enabled subset, non-persistent)

| # | Name | Mirrors | Purpose |
|---|---|---|---|
| prop1 | Page Name | eVar1 | Enables Pathing/Fallout on page name without persistence |
| prop2 | Site Section | eVar2 | Section-level pathing |
| prop3 | Product Name | eVar3 | Product pathing (e.g., "which products get viewed before abandon") |
| prop9 | Checkout Step Name | eVar9 | Checkout pathing/fallout report |
| prop12 | PLP Sort/Filter Selection | eVar12 | Fallout on filter usage before exit |

---

## 5. Products String (`s.products`) Convention

`Category;Product Name;Quantity;Price;event2=1;eVar4=SKU`

Example — Add to Cart:
`Outerwear;Trail Runner Jacket;1;129.00;event2=1|event3;eVar4=NLG-JCK-1042`

Example — Purchase (order confirmation, one entry per line item):
`Outerwear;Trail Runner Jacket;1;129.00;event9=1,purchase;eVar4=NLG-JCK-1042`

---

## 6. Page → Event/Variable Map

| Page | Fires | Variables Set |
|---|---|---|
| Home | Page View | eVar1, eVar2, eVar13 (first visit), eVar14 |
| PLP / Search Results | Page View, event8 (if from search) | eVar1, eVar2, eVar6, eVar7, prop1, prop2 |
| PLP — filter/sort applied | Link tracking, no new page view | eVar12, prop12 |
| PDP | Page View, event1 | eVar1–eVar5, prop1–prop3 |
| Add to Cart (any page) | Link tracking, event2 | eVar4, eVar8, products string |
| Cart page | Page View | eVar1, eVar8 |
| Remove from Cart | Link tracking, event3 | eVar4, eVar8, products string |
| Checkout — Shipping | Page View, event4 (step 1 only), event5 | eVar1, eVar8, eVar9=shipping, prop9 |
| Checkout — Payment | Page View, event5 | eVar9=payment, prop9 |
| Promo code field | Link tracking, event6 or event7 | eVar11 |
| Checkout — Review | Page View, event5 | eVar9=review, prop9 |
| Order Confirmation | Page View, event9, purchase (products string) | eVar1, eVar10, products string with per-item event9/purchase |
| 404 / Error page | Page View | eVar15 |

---

## 7. Open Questions / Assumptions (documented for portfolio transparency)

- No live Adobe report suite exists for this project — variable numbers (eVar1, event1, etc.) are assigned as if configuring a net-new report suite and would be validated against Admin Console's actual available variable slots in a real engagement.
- Cross-device/People-based attribution, Customer Attributes, and Data Feeds are out of scope for this portfolio piece.
- Consent/CMP gating (e.g., blocking event2 tracking pre-consent) is noted as a production requirement but not implemented in the demo site.
