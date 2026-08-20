/**
 * datalayer.js
 * -----------------------------------------------------------------------
 * The page-load data layer object that Adobe Launch data element rules
 * would read from (window.digitalData), plus a lightweight mock of the
 * Adobe Experience Platform Web SDK / _satellite API so this demo runs
 * without a real Launch library or report suite attached.
 *
 * In a production implementation:
 *   - digitalData would be populated server-side (or client-side on first
 *     paint) BEFORE the Launch embed script runs, so Data Elements can
 *     read it on library load.
 *   - _satellite.track(eventName, payload) calls below correspond 1:1 to
 *     Direct Call Rules configured in Launch (see /launch-rules/).
 *   - The "AEP Debugger" panel here stands in for what you'd actually
 *     inspect via the real Adobe Experience Platform Debugger extension.
 * -----------------------------------------------------------------------
 */

(function (window) {
  "use strict";

  // ---- 1. Page-load data layer -------------------------------------------------
  // Populated per-page by each page's inline <script> before this file's
  // DOMContentLoaded handler runs analytics initialization.
  window.digitalData = window.digitalData || {
    page: {
      pageName: "",
      section: "",
      errorCode: null,
    },
    product: [], // array of { name, sku, category, price }
    search: { term: null, resultsCount: null },
    cart: { id: getOrCreateCartId(), items: [] },
    checkout: { stepName: null },
    order: null, // { orderId, items, total }
    promo: { code: null },
    user: { visitorType: getVisitorType() },
  };

  function getOrCreateCartId() {
    let id = sessionStorage.getItem("nlg_cart_id");
    if (!id) {
      id = "cart_" + Math.random().toString(36).slice(2, 8);
      sessionStorage.setItem("nlg_cart_id", id);
    }
    return id;
  }

  function getVisitorType() {
    // Mirrors eVar14 logic: a Launch rule would check a first-party cookie.
    const seen = localStorage.getItem("nlg_returning_visitor");
    localStorage.setItem("nlg_returning_visitor", "1");
    return seen ? "returning" : "new";
  }

  function getMarketingChannel() {
    // Mirrors eVar13: parsed from utm_source/utm_medium on landing.
    const params = new URLSearchParams(window.location.search);
    const source = params.get("utm_source");
    const medium = params.get("utm_medium");
    if (!source && !medium) return null;
    return [medium, source].filter(Boolean).join("_");
  }

  // ---- 2. Mock Adobe Analytics / Launch adapter --------------------------------
  const AA = {
    events: [], // running log for the debug panel

    /** Fires a "page load" beacon — equivalent to s.t() / a Launch "Library Loaded" rule. */
    pageView: function () {
      const d = window.digitalData;
      const vars = {
        eVar1: d.page.pageName,
        eVar2: d.page.section,
        eVar13: getMarketingChannel() || undefined,
        eVar14: d.user.visitorType,
      };
      if (d.page.errorCode) vars.eVar15 = d.page.errorCode;

      if (d.product && d.product.length) {
        const p = d.product[0];
        Object.assign(vars, {
          eVar3: p.name,
          eVar4: p.sku,
          eVar5: p.category,
        });
        vars.event1 = 1; // Product View — digitalData.product is only populated on PDP
      }
      if (d.search.term) {
        vars.eVar6 = d.search.term;
        vars.eVar7 = d.search.resultsCount;
        vars.event8 = 1; // Internal Search Performed
      }
      if (d.cart.id) vars.eVar8 = d.cart.id;
      if (d.checkout.stepName) vars.eVar9 = d.checkout.stepName;
      if (d.order) vars.eVar10 = d.order.orderId;

      this._log("s.t() — Page View", vars);
    },

    /** Fires a link-tracking beacon — equivalent to s.tl() / a Launch Direct Call Rule. */
    track: function (eventName, payload) {
      payload = payload || {};
      this._log("_satellite.track('" + eventName + "')", payload);
    },

    _log: function (label, vars) {
      const entry = { time: new Date().toLocaleTimeString(), label: label, vars: vars };
      this.events.unshift(entry);
      this.events = this.events.slice(0, 30);
      renderDebugPanel();
      // eslint-disable-next-line no-console
      console.log("[AA]", label, vars);
    },
  };
  window._mockSatellite = AA; // exposed for app.js

  // ---- 3. Debug / inspector panel ----------------------------------------------
  function renderDebugPanel() {
    const list = document.getElementById("aa-debug-log");
    const dl = document.getElementById("aa-debug-datalayer");
    if (!list || !dl) return;

    list.innerHTML = AA.events
      .map(function (e) {
        const rows = Object.keys(e.vars)
          .filter((k) => e.vars[k] !== undefined && e.vars[k] !== null)
          .map((k) => `<span class="aa-var"><b>${k}</b>=${escapeHtml(String(e.vars[k]))}</span>`)
          .join("");
        return `<div class="aa-entry">
          <div class="aa-entry-head"><span class="aa-time">${e.time}</span><span class="aa-label">${escapeHtml(e.label)}</span></div>
          <div class="aa-vars">${rows || "<em>no variables set</em>"}</div>
        </div>`;
      })
      .join("");

    dl.textContent = JSON.stringify(window.digitalData, null, 2);
  }

  function escapeHtml(str) {
    return str.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  function toggleDebugPanel() {
    const panel = document.getElementById("aa-debug-panel");
    if (panel) panel.classList.toggle("open");
  }
  window.toggleDebugPanel = toggleDebugPanel;

  // ---- 4. Inject inspector panel markup (shared across every page) -------------
  function injectPanel() {
    if (document.getElementById("aa-debug-panel")) return;
    const toggle = document.createElement("div");
    toggle.id = "aa-debug-toggle";
    toggle.setAttribute("role", "button");
    toggle.setAttribute("tabindex", "0");
    toggle.innerHTML =
      '<span><span class="dot"></span>AEP Debugger (mock) — inspect what Launch would send</span><span>Click to expand ▲</span>';
    toggle.addEventListener("click", toggleDebugPanel);
    toggle.addEventListener("keypress", function (e) {
      if (e.key === "Enter" || e.key === " ") toggleDebugPanel();
    });

    const panel = document.createElement("div");
    panel.id = "aa-debug-panel";
    panel.innerHTML =
      '<div class="aa-col"><h4>Beacon Log</h4><div id="aa-debug-log"></div></div>' +
      '<div class="aa-col"><h4>window.digitalData (live)</h4><pre id="aa-debug-datalayer"></pre></div>';

    document.body.appendChild(toggle);
    document.body.appendChild(panel);
  }

  window.AA = AA;
  document.addEventListener("DOMContentLoaded", function () {
    injectPanel();
    renderDebugPanel();
  });
})(window);
