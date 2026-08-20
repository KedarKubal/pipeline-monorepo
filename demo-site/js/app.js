/**
 * app.js — Northline Goods demo storefront logic.
 * Handles cart persistence (localStorage, demo-only) and wires UI
 * interactions to the mock Adobe Analytics adapter defined in datalayer.js.
 * Each handler below corresponds to a row in tracking-plan.md section 6.
 */
(function () {
  "use strict";

  // ---- Cart storage (demo-only, real impl would call a cart API) ----
  function getCart() {
    try {
      return JSON.parse(localStorage.getItem("nlg_cart_items")) || [];
    } catch (e) {
      return [];
    }
  }
  function saveCart(items) {
    localStorage.setItem("nlg_cart_items", JSON.stringify(items));
  }
  function addToCart(sku, qty) {
    const items = getCart();
    const existing = items.find((i) => i.sku === sku);
    if (existing) existing.qty += qty;
    else items.push({ sku: sku, qty: qty });
    saveCart(items);
  }
  function removeFromCart(sku) {
    saveCart(getCart().filter((i) => i.sku !== sku));
  }
  function cartWithDetails() {
    return getCart()
      .map((i) => Object.assign({}, window.NLG_findProduct(i.sku), { qty: i.qty }))
      .filter((i) => i.sku);
  }
  function cartCount() {
    return getCart().reduce((sum, i) => sum + i.qty, 0);
  }
  function cartTotal() {
    return cartWithDetails().reduce((sum, i) => sum + i.price * i.qty, 0);
  }
  window.NLG_cart = { getCart, addToCart, removeFromCart, cartWithDetails, cartCount, cartTotal };

  // ---- Header / footer (shared chrome, injected for DRY across pages) ----
  function renderChrome(activeSection) {
    const header = document.getElementById("site-header");
    if (header) {
      header.innerHTML = `
        <a class="logo" href="index.html">Northline <span>Goods</span></a>
        <form class="search-form" id="header-search" role="search">
          <input type="text" name="q" placeholder="Search gear\u2026" aria-label="Search" />
          <button type="submit" aria-label="Search">\u2192</button>
        </form>
        <nav class="nav-links">
          <a href="plp.html?section=Outerwear" class="${activeSection === "Outerwear" ? "active" : ""}">Outerwear</a>
          <a href="plp.html?section=Gear" class="${activeSection === "Gear" ? "active" : ""}">Gear</a>
          <a href="plp.html?section=Footwear" class="${activeSection === "Footwear" ? "active" : ""}">Footwear</a>
          <a class="cart-link" href="cart.html">Cart <span class="cart-count" id="cart-count">0</span></a>
        </nav>`;
      const form = document.getElementById("header-search");
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        const q = form.q.value.trim();
        if (q) window.location.href = "plp.html?q=" + encodeURIComponent(q);
      });
      const countEl = document.getElementById("cart-count");
      if (countEl) countEl.textContent = cartCount();
    }
    const footer = document.getElementById("site-footer");
    if (footer) {
      footer.innerHTML = `Northline Goods \u2014 Adobe Analytics tracking-plan demo site. Not a real store. Built to exercise a full measurement implementation, not to sell jackets.`;
    }
  }
  window.NLG_renderChrome = renderChrome;

  // ---- Product card / row templates ----
  function productCardHtml(p) {
    return `<a class="product-card" href="pdp.html?sku=${encodeURIComponent(p.sku)}" data-sku="${p.sku}">
      <div class="swatch">${p.image}</div>
      <div class="cat">${p.category}</div>
      <h3>${p.name}</h3>
      <div class="price">$${p.price.toFixed(2)}</div>
    </a>`;
  }
  window.NLG_productCardHtml = productCardHtml;

  document.addEventListener("DOMContentLoaded", function () {
    renderChrome(document.body.dataset.section || null);
  });
})();
