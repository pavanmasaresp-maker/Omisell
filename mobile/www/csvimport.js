// Marketplace ki order CSV file ko app ke order format mein badalna. Kisi marketplace ka fixed template nahi maanta:
// columns ka mapping seller khud confirm karta hai (header se andaza lagake bhara aata hai).
const CsvImport = (() => {
  const FIELDS = [
    { k: "id", label: "Order ID", req: true, re: [/^orderid$/, /^ordernumber$/, /^orderno$/, /^suborderno$/, /^orderitemid$/, /^referenceno$/, /^id$/, /orderid/, /orderno/, /ordernum/] },
    { k: "sku", label: "SKU code", req: true, re: [/^sku$/, /^sellersku$/, /^merchantsku$/, /^skucode$/, /^productsku$/, /sku/] },
    { k: "qty", label: "Quantity", req: true, re: [/^(qty|quantity)$/, /^(units|itemquantity|orderquantity)$/, /qty|quantity/] },
    { k: "price", label: "Price (per piece)", req: false, re: [/^unitprice$/, /^sellingprice$/, /^itemprice$/, /^saleprice$/, /^price$/, /price/] },
    { k: "name", label: "Customer name", req: false, re: [/^customername$/, /^buyername$/, /^recipientname$/, /^shippingname$/, /^name$/, /customername|buyer|recipient/] },
    { k: "phone", label: "Phone", req: false, re: [/phone|mobile|contact/] },
    { k: "city", label: "City", req: false, re: [/^city$/, /^shippingcity$/, /^deliverycity$/, /city|town/] },
  ];
  const norm = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9]/g, "");

  function parse(text) {
    text = String(text || "").replace(/^﻿/, "");
    const first = text.split(/\r?\n/, 1)[0] || "";
    const delim = [",", ";", "\t"].map((d) => [d, first.split(d).length]).sort((a, b) => b[1] - a[1])[0][0];
    const rows = []; let r = [], f = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
      else if (c === '"') q = true;
      else if (c === delim) { r.push(f); f = ""; }
      else if (c === "\n") { r.push(f); rows.push(r); r = []; f = ""; }
      else if (c !== "\r") f += c;
    }
    if (f !== "" || r.length) { r.push(f); rows.push(r); }
    return rows.filter((x) => x.some((c) => String(c).trim() !== ""));
  }

  function guess(headers) {
    const h = headers.map(norm), used = new Set(), map = {};
    for (const fd of FIELDS) {
      map[fd.k] = -1;
      for (const re of fd.re) {
        const i = h.findIndex((x, ix) => !used.has(ix) && x && re.test(x));
        if (i >= 0) { map[fd.k] = i; used.add(i); break; }
      }
    }
    return map;
  }

  const money = (v) => { const n = parseFloat(String(v || "").replace(/[^0-9.\-]/g, "")); return Number.isFinite(n) && n >= 0 ? n.toFixed(2) : null; };

  function build(rows, map) {
    const out = new Map(); let lines = 0, skipped = 0;
    const cell = (r, k) => (map[k] >= 0 && map[k] < r.length ? String(r[map[k]] ?? "").trim() : "");
    for (const r of rows.slice(1)) {
      const id = cell(r, "id"), sku = cell(r, "sku"), qty = parseInt(String(cell(r, "qty")).replace(/[^0-9]/g, ""), 10);
      if (!id || !sku || !(qty > 0)) { skipped++; continue; }
      if (!out.has(id)) out.set(id, { external_order_id: id, customer_name: "", customer_phone: "", shipping_address: {}, items: [] });
      const o = out.get(id);
      if (!o.customer_name) o.customer_name = cell(r, "name").slice(0, 200);
      if (!o.customer_phone) o.customer_phone = cell(r, "phone").slice(0, 32);
      const city = cell(r, "city"); if (city && !o.shipping_address.city) o.shipping_address.city = city.slice(0, 200);
      const price = money(cell(r, "price"));
      const same = o.items.find((i) => i.sku_code === sku);
      if (same) same.quantity += qty; else o.items.push({ sku_code: sku.slice(0, 100), quantity: qty, ...(price ? { unit_price: price } : {}) });
      lines++;
    }
    return { orders: [...out.values()], lines, skipped };
  }
  return { FIELDS, parse, guess, build };
})();
if (typeof module !== "undefined") module.exports = CsvImport;
