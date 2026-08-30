# Processing Rules — northlinegoods-prod

Configured in Admin Console → Report Suites → Edit Settings → General → Processing Rules.
These run server-side, after the beacon is received and before the hit is written to the
report suite, so they're the right place for cleanup that shouldn't depend on every Launch
rule author getting it exactly right client-side.

| # | Condition | Action | Rationale |
|---|---|---|---|
| 1 | `eVar6` (Internal Search Term) contains value | Lowercase and trim `eVar6` | Client-side lowercasing already happens in `plp.html`, but this is a server-side backstop against future rule changes that skip it — avoids `"Jacket"` and `"jacket"` splitting the same search term across two rows. |
| 2 | `eVar11` (Promo Code) contains value | Uppercase `eVar11` | Promo codes are entered free-text; normalizes `welcome10` / `WELCOME10` / `Welcome10` into one value for Promo reporting. |
| 3 | Page Name (eVar1) is empty AND URL contains `/pdp.html` | Overwrite Page Name with `"PDP: Unknown SKU"` | Safety net for a PDP hit that fires before the product data element resolves (e.g., a slow-loading catalog call) — keeps rows out of "unspecified" the report suite would otherwise show. |
| 4 | `eVar4` (Product SKU) contains value AND `eVar5` (Product Category) is empty | Set eVar5 to `"Uncategorized"` | Prevents orphaned SKUs (e.g., a newly added product missing a category) from breaking category-level rollups. |

## Why processing rules instead of more Launch rules

- Processing rules apply retroactively to *how* existing variables are cleaned, without a
  Launch library re-publish — useful for fast-turnaround data-quality fixes.
- They keep normalization logic in one place (Admin Console) rather than duplicated across
  every Launch rule that happens to set `eVar6` or `eVar11`.
- They are not a substitute for fixing the root cause client-side; each rule above has a
  matching implementation note in `tracking-plan.md` / the data layer so both layers agree.
