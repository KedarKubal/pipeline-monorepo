/**
 * products-data.js
 * Static catalog for the Northline Goods demo. Stands in for a real PIM/API.
 */
window.NLG_PRODUCTS = [
  {
    sku: "NLG-JCK-1042",
    name: "Trail Runner Jacket",
    category: "Outerwear/Jackets",
    section: "Outerwear",
    price: 129.0,
    blurb: "Packable 2.5-layer shell built for fast-moving weather.",
    image: "jacket",
  },
  {
    sku: "NLG-JCK-1077",
    name: "Ridgeline Down Parka",
    category: "Outerwear/Jackets",
    section: "Outerwear",
    price: 249.0,
    blurb: "650-fill down for standing still in the cold.",
    image: "parka",
  },
  {
    sku: "NLG-PCK-2011",
    name: "Summit 32L Pack",
    category: "Gear/Packs",
    section: "Gear",
    price: 179.0,
    blurb: "A day pack that carries like it's half its size.",
    image: "pack",
  },
  {
    sku: "NLG-BTS-3005",
    name: "Basecamp Waterproof Boot",
    category: "Footwear/Boots",
    section: "Footwear",
    price: 159.0,
    blurb: "Wet trailheads, dry feet.",
    image: "boot",
  },
  {
    sku: "NLG-FLC-1090",
    name: "Alpine Fleece Half-Zip",
    category: "Outerwear/Midlayers",
    section: "Outerwear",
    price: 89.0,
    blurb: "The midlayer that never comes off the chair.",
    image: "fleece",
  },
  {
    sku: "NLG-BTL-4002",
    name: "Insulated Field Bottle",
    category: "Gear/Hydration",
    section: "Gear",
    price: 39.0,
    blurb: "Cold at noon, cold at dusk.",
    image: "bottle",
  },
];

window.NLG_findProduct = function (sku) {
  return window.NLG_PRODUCTS.find((p) => p.sku === sku);
};
