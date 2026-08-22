/**
 * cart-tracking-flag.spec.js
 * -----------------------------------------------------------------------
 * Integration test for the coupling between the Adobe Analytics demo site
 * and the Config Toggle Service: the "cart-tracking-enabled" flag must
 * gate whether the event2 ("cart.add") beacon fires when a user adds an
 * item to their cart.
 *
 * Requires the full stack running (`docker compose up -d` from the repo
 * root) — this hits the REAL toggle-service over HTTP, the same way the
 * browser does, rather than mocking it. That's deliberate: the thing
 * under test IS the network coupling, so mocking it away would defeat
 * the point of the test.
 * -----------------------------------------------------------------------
 */

const { test, expect } = require("@playwright/test");

const DEMO_SITE_URL = "http://localhost:8000";
const TOGGLE_SERVICE_URL = "http://localhost:3000";
const FLAG_KEY = "cart-tracking-enabled";
const API_KEY = process.env.TOGGLE_SERVICE_API_KEY || "dev-local-key";

/** Sets the flag's enabled state directly via the toggle-service write API. */
async function setFlagEnabled(request, enabled) {
  const res = await request.patch(`${TOGGLE_SERVICE_URL}/api/flags/${FLAG_KEY}`, {
    headers: { "X-API-Key": API_KEY, "Content-Type": "application/json" },
    data: { enabled },
  });
  expect(res.ok(), `Failed to set flag enabled=${enabled}: ${res.status()}`).toBeTruthy();
}

/** Reads the recorded beacon log from the mock Adobe Analytics adapter. */
async function getBeaconEvents(page) {
  return page.evaluate(() => window._mockSatellite.events);
}

/** Finds the first in-stock product's PDP URL by scraping the PLP grid. */
async function firstProductPdpUrl(page) {
  await page.goto(`${DEMO_SITE_URL}/plp.html`);
  const href = await page.locator(".product-card").first().getAttribute("href");
  return `${DEMO_SITE_URL}/${href}`;
}

test.describe("cart-tracking-enabled flag gates the cart.add beacon", () => {
  // Restore the flag to a known state after the suite runs, so this test
  // doesn't leave toggle-service in whatever state the last assertion needed.
  test.afterAll(async ({ request }) => {
    await setFlagEnabled(request, true);
  });

  test("fires the cart.add / event2 beacon when the flag is enabled", async ({ page, request }) => {
    await setFlagEnabled(request, true);

    const pdpUrl = await firstProductPdpUrl(page);
    await page.goto(pdpUrl);

    await page.getByRole("button", { name: "Add to Cart" }).click();

    // fetchFlag() is async, so give the click handler a moment to resolve
    // the fetch and push the tracking call before we inspect the log.
    await expect
      .poll(async () => (await getBeaconEvents(page)).some((e) => e.label.includes("cart.add")))
      .toBe(true);

    const events = await getBeaconEvents(page);
    const cartAddEvent = events.find((e) => e.label.includes("cart.add"));
    expect(cartAddEvent.vars.event2).toBeGreaterThan(0);
    expect(cartAddEvent.vars.eVar4).toBeTruthy(); // SKU should be set
  });

  test("suppresses the cart.add / event2 beacon when the flag is disabled", async ({ page, request }) => {
    await setFlagEnabled(request, false);

    const pdpUrl = await firstProductPdpUrl(page);
    // Fresh navigation (not just a click) ensures fetchFlag's in-memory
    // cache from any prior test doesn't mask a bug — cache is per page load.
    await page.goto(pdpUrl);

    await page.getByRole("button", { name: "Add to Cart" }).click();

    // Give fetchFlag's request a moment to resolve before asserting absence,
    // otherwise a slow network could produce a false pass.
    await page.waitForTimeout(500);

    const events = await getBeaconEvents(page);
    const cartAddEvent = events.find((e) => e.label.includes("cart.add"));
    expect(cartAddEvent).toBeUndefined();

    // The cart item should still be added — the flag only gates tracking,
    // never the actual user-facing functionality (fail-open by design).
    const cartCountText = await page.locator("#cart-count").textContent();
    expect(Number(cartCountText)).toBeGreaterThan(0);
  });

  test("fails open (tracking stays enabled, add-to-cart still works) when toggle-service is unreachable", async ({ page }) => {
    await setFlagEnabled(page.request, true); // flag itself is irrelevant here — service is unreachable either way

    // Simulate toggle-service being down by aborting requests to it at the
    // network layer — the same failure fetchFlag() would see from a stopped
    // container — without needing shell access to actually stop it mid-test.
    await page.route(`${TOGGLE_SERVICE_URL}/**`, (route) => route.abort("connectionrefused"));

    const pdpUrl = await firstProductPdpUrl(page);
    await page.goto(pdpUrl);

    await page.getByRole("button", { name: "Add to Cart" }).click();

    // fetchFlag() must reject, catch, and resolve to fail-open before the
    // beacon fires — poll rather than a fixed timeout since the exact
    // rejection timing can vary.
    await expect
      .poll(async () => (await getBeaconEvents(page)).some((e) => e.label.includes("cart.add")))
      .toBe(true);

    const events = await getBeaconEvents(page);
    const cartAddBeacon = events.find((e) => e.label.includes("cart.add"));
    expect(cartAddBeacon).toBeDefined();
    expect(cartAddBeacon.vars.event2).toBeGreaterThan(0);

    const cartCountText = await page.locator("#cart-count").textContent();
    expect(Number(cartCountText)).toBeGreaterThan(0);

    await page.unroute(`${TOGGLE_SERVICE_URL}/**`);
  });
});
