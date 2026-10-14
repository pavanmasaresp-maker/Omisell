// ================= API client =================
const BASE = (typeof API_URL !== "undefined" ? API_URL : "") + "/api/v1";
const getToken = () => { try { return localStorage.getItem("omnisell_token"); } catch { return null; } };
const saveToken = (t) => { try { localStorage.setItem("omnisell_token", t); } catch {} };
const clearToken = () => { try { localStorage.removeItem("omnisell_token"); Object.keys(localStorage).filter((k) => k.startsWith("omnisell_home_")).forEach((k) => localStorage.removeItem(k)); } catch {} };

async function req(path, opts = {}) {
  const token = getToken();
  let res;
  try {
    res = await fetch(BASE + path, {
      ...opts,
      headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Token ${token}` } : {}) },
    });
  } catch {
    throw new Error("Server tak nahi pahunch paye. Internet check karo, aur backend chal raha hai ya nahi dekho.");
  }
  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch {}
  if (res.status === 401 && token) { clearToken(); showLogin(); throw new Error("Session khatam. Dobara sign in karo."); }
  if (!res.ok) {
    const first = typeof data === "object" && data && !data.error && !data.detail
      ? Object.entries(data).map(([k, v]) => `${k}: ${[].concat(v).join(" ")}`).join(" · ") : "";
    throw new Error(data.error || data.detail || first || `HTTP ${res.status}: ${text.slice(0, 160)}`);
  }
  return data;
}
const list = (d) => (Array.isArray(d) ? d : d.results || []);
const send = (method) => (path, body) => req(path, { method, body: body ? JSON.stringify(body) : undefined });
const post = send("POST"), patch = send("PATCH"), del = send("DELETE");

const api = {
  login: (username, password) => post("/auth/login", { username, password }),
  me: () => req("/auth/me"),
  googleLogin: (id_token) => post("/auth/google", { id_token }),
  deleteAccount: () => del("/auth/me", { confirm: "DELETE" }),
  dashboard: () => req("/dashboard"),
  overview: (days) => req(`/dashboard/overview?days=${days}`),
  setFees: (id, commission_pct, charge_per_order) => post(`/channels/connections/${id}/fees`, { commission_pct, charge_per_order }),
  products: async (q = "") => list(await req("/products" + (q ? `?search=${encodeURIComponent(q)}` : ""))),
  updateProduct: (id, b) => patch(`/products/${id}`, b),
  deleteProduct: (id) => del(`/products/${id}`),
  skus: async () => list(await req("/skus")),
  updateSku: (id, b) => patch(`/skus/${id}`, b),
  createProductWithSku: async ({ title, skuCode, price }) => {
    const p = await post("/products", { title, status: "DRAFT" });
    const v = await post("/variants", { product: p.id, name: "Default" });
    return post("/skus", { variant: v.id, sku_code: skuCode, price });
  },
  balances: async () => list(await req("/inventory/")),
  ledger: async (sku) => list(await req(`/inventory/ledger?sku=${sku}`)),
  adjust: (sku, delta, reason = "mobile app") =>
    post("/inventory/adjust", { sku, entry_type: "ADJUSTMENT", quantity_delta: delta, reason, idempotency_key: `${sku}-${Date.now()}` }),
  orders: async (status = "") => list(await req("/orders" + (status ? `?status=${status}` : ""))),
  createOrder: (b) => post("/orders", { ...b, idempotency_key: `mob-${Date.now()}` }),
  orderStep: (id, step, body) => post(`/orders/${id}/${step}`, body),
  cancelOrder: (id, reason) => post(`/orders/${id}/cancel`, { reason }),
  connections: async () => list(await req("/channels/connections")),
  createConnection: (b) => post("/channels/connections", b),
  checkConnection: (id) => post(`/channels/connections/${id}/check`),
  deleteConnection: (id) => del(`/channels/connections/${id}`),
  setAuto: (id, level) => post(`/channels/connections/${id}/auto-process`, { auto_process: level }),
  setAutoPublish: (id, enabled) => post(`/channels/connections/${id}/auto-publish`, { enabled }),
  publishAll: (id) => post(`/channels/connections/${id}/publish-all`),
  importOrders: (id, orders) => post(`/channels/connections/${id}/import-orders`, { orders }),
  pullOrders: (id) => post(`/channels/connections/${id}/pull-orders`),
  simulateOrder: (id) => post(`/channels/connections/${id}/simulate-order`),
  jobs: async () => list(await req("/channels/jobs")),
  retryJob: (id) => post(`/channels/jobs/${id}/retry`),
  listings: async () => list(await req("/channels/listings")),
  publish: (product, connection) => post("/channels/publish", { product, connection }),
};

// ================= helpers =================
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = (n) => "₹" + Number(n || 0).toLocaleString("en-IN", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
const num = (n) => Number(n || 0).toLocaleString("en-IN");
const content = () => $("content");

const TONE = {
  DRAFT: ["#5B6485", "#ECEEF4"], ACTIVE: ["#12733F", "#E3F4EA"], ARCHIVED: ["#8A92AE", "#ECEEF4"],
  IMPORTED: ["#27489E", "#E6ECFB"], CONFIRMED: ["#27489E", "#E6ECFB"], PACKED: ["#9A5B00", "#FFF1D6"],
  SHIPPED: ["#1B2559", "#DDE2F5"], DELIVERED: ["#12733F", "#E3F4EA"], CANCELLED: ["#B42318", "#FDECEA"], RETURNED: ["#B42318", "#FDECEA"],
  PENDING: ["#5B6485", "#ECEEF4"], RUNNING: ["#27489E", "#E6ECFB"], SUCCEEDED: ["#12733F", "#E3F4EA"], FAILED: ["#B42318", "#FDECEA"],
  NEEDS_ACTION: ["#9A5B00", "#FFF1D6"], CONNECTED: ["#12733F", "#E3F4EA"], ERROR: ["#B42318", "#FDECEA"],
};
const pill = (s) => { const [fg, bg] = TONE[s] || TONE.DRAFT; return `<span class="pill" style="color:${fg};background:${bg}">${esc(String(s || "").replace("_", " "))}</span>`; };
const empty = (title, hint = "") => `<div class="empty"><b>${esc(title)}</b>${esc(hint)}</div>`;
const errBanner = (m) => (m ? `<div class="banner err">${esc(m)}</div>` : "");
const loading = () => (content().innerHTML = `<div class="loading">Loading…</div>`);
const skusOf = (p) => (p.variants || []).flatMap((v) => v.skus || []);

let toastT;
function toast(msg, isErr) {
  const t = $("toast"); t.textContent = msg; t.className = "toast" + (isErr ? " err" : "");
  clearTimeout(toastT); toastT = setTimeout(() => t.classList.add("hidden"), 3200);
}

function sheet(inner) {
  const o = document.createElement("div");
  o.className = "overlay";
  o.innerHTML = `<div class="sheet"><div class="grab"></div>${inner}</div>`;
  o.addEventListener("click", (e) => { if (e.target === o) o.remove(); });
  document.body.appendChild(o);
  return o;
}
function sheetErr(o, m) {
  let b = o.querySelector(".sheet-err");
  if (!b) { b = document.createElement("div"); b.className = "banner err sheet-err"; o.querySelector(".sheet").insertBefore(b, o.querySelector(".sheet-actions")); }
  b.textContent = m;
}
async function busy(btn, fn) {
  const label = btn.innerHTML; btn.disabled = true; btn.textContent = "Please wait…";
  try { await fn(); } finally { btn.disabled = false; btn.innerHTML = label; }
}

// ================= auth =================
async function doLogin() {
  const u = $("login-username").value.trim(), p = $("login-password").value;
  const box = $("login-err"); box.classList.add("hidden");
  if (!u || !p) { box.textContent = "Username aur password dono daalo."; box.classList.remove("hidden"); return; }
  await busy($("login-btn"), async () => {
    try { const r = await api.login(u, p); saveToken(r.token); showApp(); }
    catch (e) { box.textContent = e.message; box.classList.remove("hidden"); }
  });
}
// Plain-JS Capacitor: plugin proxy "Capacitor.Plugins.<Name>" se milta hai (registerPlugin sirf bundler wale apps mein hota hai).
function getFA() {
  const C = window.Capacitor;
  if (!C) return null;
  try { if (C.Plugins && C.Plugins.FirebaseAuthentication) return C.Plugins.FirebaseAuthentication; } catch (_) {}
  try { if (typeof C.registerPlugin === "function") return C.registerPlugin("FirebaseAuthentication"); } catch (_) {}
  return null;
}
async function googleLogin() {
  const box = $("login-err"); box.classList.add("hidden");
  const fail = (m) => { box.textContent = m; box.classList.remove("hidden"); };
  const C = window.Capacitor;
  let plat = "none";
  try { plat = C ? (C.getPlatform ? C.getPlatform() : (C.isNativePlatform && C.isNativePlatform() ? "native" : "?")) : "none"; } catch (_) {}
  if (!getFA() || plat === "web" || plat === "none") {
    return fail("Google login sirf phone ki app mein chalta hai (platform: " + plat + "). Browser mein neeche Admin login use karo.");
  }
  await busy($("google-btn"), async () => {
    try {
      await getFA().signInWithGoogle();
      const { token } = await getFA().getIdToken({ forceRefresh: true });
      const r = await api.googleLogin(token);
      saveToken(r.token); showApp();
    } catch (e) {
      const m = String((e && e.message) || e || "");
      if (/cancel/i.test(m)) return;
      fail(m.includes("Server tak") ? m : "Google login nahi ho paya: " + m.slice(0, 160));
    }
  });
}
async function emailAuth(mode) {
  const box = $("login-err"); box.classList.add("hidden");
  const fail = (m) => { box.textContent = m; box.classList.remove("hidden"); };
  const email = $("em-email").value.trim(), pass = $("em-pass").value;
  if (!getFA()) return fail("Ye option sirf phone ki app mein chalta hai.");
  if (!email) return fail("Email daalo.");
  if (mode !== "reset" && pass.length < 6) return fail("Password kam se kam 6 akshar ka hona chahiye.");
  const btn = $(mode === "in" ? "em-in" : mode === "up" ? "em-up" : "em-in");
  await busy(btn, async () => {
    try {
      if (mode === "reset") {
        await getFA().sendPasswordResetEmail({ email });
        return fail("Password reset ka link email par bhej diya. Inbox / spam dekho.");
      }
      if (mode === "up") {
        await getFA().createUserWithEmailAndPassword({ email, password: pass });
        await getFA().sendEmailVerification();
        await getFA().signOut();
        return fail("Account ban gaya. Email par verify link bheja hai: use khol kar verify karo, phir Sign in dabao.");
      }
      const r = await getFA().signInWithEmailAndPassword({ email, password: pass });
      if (!r.user || !r.user.emailVerified) {
        try { await getFA().sendEmailVerification(); } catch (_) {}
        await getFA().signOut();
        return fail("Email abhi verify nahi hui. Naya verify link bheja hai: inbox / spam dekho, verify karke dobara Sign in karo.");
      }
      const { token } = await getFA().getIdToken({ forceRefresh: true });
      const res = await api.googleLogin(token);
      saveToken(res.token); showApp();
    } catch (e) {
      const m = String((e && (e.message || e.code)) || e || "");
      if (/email-already-in-use/i.test(m)) fail("Is email se account pehle se hai. Sign in karo.");
      else if (/invalid-credential|wrong-password|user-not-found|supplied auth credential|auth credential is incorrect|malformed or has expired|INVALID_LOGIN/i.test(m)) fail("Email ya password galat hai. Email ki spelling check karo (jaise gmail.com). Naya ho to pehle Create account dabao.");
      else if (/invalid-email|badly formatted/i.test(m)) fail("Email sahi format mein nahi hai.");
      else if (/network-request-failed|network error/i.test(m)) fail("Internet nahi chal raha. Check karke dobara try karo.");
      else if (/user-disabled/i.test(m)) fail("Ye account band kar diya gaya hai.");
      else if (/weak-password/i.test(m)) fail("Password kamzor hai, kam se kam 6 akshar rakho.");
      else if (/too-many-requests/i.test(m)) fail("Bahut koshish ho gayi. Thodi der baad try karo.");
      else fail(m.includes("Server tak") ? m : "Nahi ho paya: " + m.slice(0, 160));
    }
  });
}
async function checkAuth() {
  if (!getToken()) return showLogin();
  try { await api.me(); showApp(); } catch { clearToken(); showLogin(); }
}
function showLogin() {
  document.querySelectorAll(".overlay").forEach((o) => o.remove());
  $("login-screen").classList.remove("hidden"); $("app-screen").classList.add("hidden");
}
function showApp() {
  $("login-screen").classList.add("hidden"); $("app-screen").classList.remove("hidden");
  try { fetch(API_URL + "/healthz", { mode: "no-cors" }).catch(() => {}); } catch {}  // free server so raha ho to jaga do
  go("home");
  if (window.Tour) Tour.maybe();
}
async function logout() {
  try { if (getFA()) await getFA().signOut(); } catch {}
  clearToken(); showLogin();
}

// ================= navigation =================
let view = "home", skuCache = [], orderFilter = "";
const TITLES = {
  home: ["Home", "Aapki dukaan ka aaj ka haal"], products: ["Products", ""], stock: ["Stock", "Kitna maal hai"],
  orders: ["Orders", ""], more: ["More", ""], channels: ["Channels", "Jahan aap bechte ho"], sync: ["Sync", "Product channel par bhejo"], settings: ["Settings", "Bhasha, guide, account"],
};
const MAIN = ["home", "products", "stock", "orders", "more"];
function go(v) {
  view = v;
  const tab = MAIN.includes(v) ? v : "more";
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("on", t.dataset.tab === tab));
  $("back-btn").classList.toggle("hidden", MAIN.includes(v));
  $("topbar-title").textContent = TITLES[v][0]; $("topbar-sub").textContent = TITLES[v][1];
  content().scrollTop = 0; loading();
  ({ home: renderHome, products: () => renderProducts(""), stock: renderStock, orders: () => renderOrders(orderFilter),
     more: renderMore, channels: renderChannels, sync: renderSync, settings: renderSettings })[v]();
}
function goBack() { go("more"); }
const setSub = (t) => ($("topbar-sub").textContent = t);

// ================= Home (seller dashboard) =================
let dashDays = 30, dashTab = "channels";
const CH_ICON = { FLIPKART: "🛒", SHOPIFY: "🛍️", WOOCOMMERCE: "🌐", DEMO: "🧪", FILE: "📄", DIRECT: "🏪" };
const PIPE = [["IMPORTED", "Naya", "var(--info)"], ["CONFIRMED", "Confirmed", "var(--info)"], ["PACKED", "Packed", "var(--warn)"],
  ["SHIPPED", "Raste mein", "var(--accent)"], ["DELIVERED", "Delivered", "var(--ok)"], ["CANCELLED", "Cancel", "var(--danger)"], ["RETURNED", "Return", "var(--danger)"]];
function setDash(k, v) { if (k === "days") dashDays = v; else dashTab = v; renderHome(); }
async function renderHome() {
  const ck = `omnisell_home_${dashDays}_${dashTab}`;
  try { const c = localStorage.getItem(ck); if (c) content().innerHTML = c; } catch {}  // pichla data turant, naya peeche se
  try {
    const [d, o] = await Promise.all([api.dashboard(), api.overview(dashDays)]);
    const t = o.totals, ch = o.channels || [], pl = o.pipeline || {};
    const onHand = d.total_on_hand ?? 0, res = d.total_reserved ?? 0, avail = Math.max(onHand - res, 0);
    const low = d.low_stock || [];
    const pmax = Math.max(1, ...PIPE.map((p) => pl[p[0]] || 0));
    const cmax = Math.max(1, ...ch.map((c) => Number(c.revenue)));
    const chips = [[7, "7 din"], [30, "30 din"], [0, "Sab"]].map(([v, l]) => `<button class="chip ${dashDays === v ? "on" : ""}" onclick="setDash('days',${v})">${l}</button>`).join("");
    const tabs = [["channels", "Channels"], ["products", "Products"], ["stock", "Stock"]].map(([v, l]) => `<button class="chip ${dashTab === v ? "on" : ""}" onclick="setDash('tab','${v}')">${l}</button>`).join("");
    let body = "";
    if (dashTab === "channels") {
      body = ch.length ? ch.map((c) => `<div class="card dcard">
        <div class="row between"><div class="grow"><div class="name">${CH_ICON[c.channel] || "🛒"} ${esc(c.name)}</div>
          <div class="small">${num(c.orders)} order · ${num(c.units)} piece bika</div></div>
          <div style="text-align:right"><div class="name num">${money(c.revenue)}</div><div class="small">Sale</div></div></div>
        <div class="meter"><i style="width:${Math.round((Number(c.revenue) / cmax) * 100)}%"></i></div>
        <div class="kv"><div><span class="small">Charges</span><b class="num" style="color:var(--danger)">−${money(c.fees)}</b></div>
          <div><span class="small">Aapko bacha</span><b class="num" style="color:var(--ok)">${money(c.net)}</b></div></div>
        <div class="dchips">
          <span class="dc ok">Delivered ${num(c.delivered)}</span><span class="dc warn">Raste mein ${num(c.in_transit)}</span>
          <span class="dc info">Bhejna baaki ${num(c.to_ship)}</span>${c.returned ? `<span class="dc bad">Return ${num(c.returned)}</span>` : ""}${c.cancelled ? `<span class="dc bad">Cancel ${num(c.cancelled)}</span>` : ""}</div>
        ${c.channel !== "DIRECT" && c.channel !== "FILE" ? `<div class="small" style="margin-top:8px">Listed: <b>${num(c.listed)}</b>${c.pending ? ` · Pending ${num(c.pending)}` : ""}${c.failed ? ` · <span style="color:var(--danger)">Fail ${num(c.failed)}</span>` : ""}</div>` : ""}
        ${c.channel !== "DIRECT" ? `<div class="small muted" style="margin-top:6px">Charge setting: ${esc(c.commission_pct)}% + ${money(c.charge_per_order)} har order <a href="#" onclick="event.preventDefault();feeSheet('${c.id}',${esc(JSON.stringify(c.name))},'${esc(c.commission_pct)}','${esc(c.charge_per_order)}')" class="lnk">badlo</a></div>` : ""}
      </div>`).join("") : empty("Koi channel nahi", "Channels mein jaake apna store ya CSV channel connect karo.");
    } else if (dashTab === "products") {
      body = (o.top_products || []).length ? `<div class="section" style="margin-top:0">Sabse zyada bika</div><div class="card">${o.top_products.map((p, i) => `<div class="ledger-row"><div class="grow">${i + 1}. ${esc(p.product)}</div><div class="num"><b>${num(p.units)}</b> pcs · ${money(p.revenue)}</div></div>`).join("")}</div>` : "";
      body += `<div class="section">Kaunsa product kahan hai</div>` + ((o.products || []).length ? o.products.map((p) => `<div class="card"><div class="row between"><div class="grow"><div class="name">${esc(p.title)}</div><div class="small">${num(p.sold)} bika</div></div>${pill(p.status || "DRAFT")}</div>
        <div class="dchips">${p.channels.length ? p.channels.map((c) => `<span class="dc ${c.status === "ACTIVE" ? "ok" : c.status === "PENDING" ? "warn" : "bad"}">${esc(c.channel)} · ${c.status === "ACTIVE" ? "Live" : c.status === "PENDING" ? "Pending" : "Fail"}</span>`).join("") : `<span class="dc">Kisi channel par nahi</span>`}</div></div>`).join("") : empty("Abhi koi product nahi", "Products tab se add karo."));
    } else {
      body = `<div class="card"><div class="row between"><div><div class="small">Bechne layak stock</div><div class="big2 num">${num(avail)}</div></div><div style="text-align:right" class="small">On hand ${num(onHand)}<br>Orders ke liye ruka ${num(res)}</div></div></div>
        <div class="section">Kam bacha (≤ ${esc(d.low_stock_threshold ?? "")})</div>` +
        (low.length ? low.map((i) => `<div class="card accent ${i.available <= 0 ? "red" : ""}"><div class="row between"><div class="grow"><div class="name">${esc(i.sku_code)}</div><div class="small">${esc(i.product)}</div></div><div class="num" style="font-size:22px;font-weight:800;color:${i.available <= 0 ? "var(--danger)" : "var(--warn)"}">${num(i.available)}</div></div></div>`).join("") : empty("Stock theek hai", "Koi SKU kam nahi pada."));
    }
    content().innerHTML = `
      <div class="row" style="gap:6px;margin-bottom:10px">${chips}</div>
      <div class="hero">
        <div class="k">Total sale</div><div class="big num">${money(t.revenue)}</div>
        <div class="meta"><span>Charges −${money(t.fees)}</span><span>Aapko bacha ${money(t.net)}</span></div>
      </div>
      <div class="tiles t3">
        <button class="tile" onclick="go('products')"><div class="l">Products</div><div class="v num">${num(t.products)}</div><div class="small">${num(t.listed_products)} live</div></button>
        <button class="tile" onclick="go('orders')"><div class="l">Orders</div><div class="v num">${num(t.orders)}</div></button>
        <button class="tile"><div class="l">Pieces</div><div class="v num">${num(t.units)}</div></button>
      </div>
      <div class="section">Delivery ka haal</div>
      <div class="card">${PIPE.map(([k, l, col]) => `<div class="prow"><span class="pl">${l}</span><span class="pbar"><i style="width:${Math.round(((pl[k] || 0) / pmax) * 100)}%;background:${col}"></i></span><b class="num">${num(pl[k] || 0)}</b></div>`).join("")}</div>
      <div class="row" style="gap:6px;margin:14px 0 10px">${tabs}</div>
      ${body}`;
    try { localStorage.setItem(ck, content().innerHTML); } catch {}
  } catch (e) { content().innerHTML = errBanner(e.message) + `<button class="btn quiet" onclick="go('home')">Try again</button>`; }
}
function feeSheet(id, name, pct, per) {
  const o = sheet(`<h3>Charges: ${esc(name)}</h3>
    <div class="hint">Marketplace jo commission/charge leta hai wo yahan daalo (seller panel ya invoice se dekh lo). Dashboard isi se "aapko bacha" nikalta hai. Ye sirf hisaab ke liye hai, marketplace par kuch nahi badalta.</div>
    <label class="lbl">Commission (% of sale)</label><input id="f-pct" inputmode="decimal" value="${esc(pct)}" />
    <label class="lbl">Har order par fixed charge (₹)</label><input id="f-per" inputmode="decimal" value="${esc(per)}" />
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn quiet" id="f-cancel">Cancel</button><button class="btn" id="f-save">Save</button></div>`);
  o.querySelector("#f-cancel").onclick = () => o.remove();
  o.querySelector("#f-save").onclick = (e) => busy(e.target, async () => {
    try { await api.setFees(id, o.querySelector("#f-pct").value.trim() || "0", o.querySelector("#f-per").value.trim() || "0"); o.remove(); toast("Charges save ho gaye"); renderHome(); }
    catch (er) { sheetErr(o, er.message); }
  });
}

// ================= Products =================
let prodSearch = "", openProduct = null;
async function renderProducts(q = prodSearch) {
  prodSearch = q;
  try {
    const products = await api.products(q);
    setSub(products.length === 1 ? "1 product" : `${products.length} products`);
    content().innerHTML = `
      <input id="psearch" placeholder="Naam ya SKU se dhundo" value="${esc(q)}" enterkeyhint="search" />
      <button class="btn" onclick="showAddProduct()">Add product</button>
      <div style="height:12px"></div>
      ${products.length ? products.map((p) => productCard(p)).join("") : empty(q ? "Kuch nahi mila" : "Abhi koi product nahi", q ? "Dusra naam ya SKU try karo." : "Pehla product add karke shuru karo.")}`;
    $("psearch").addEventListener("keydown", (e) => { if (e.key === "Enter") renderProducts(e.target.value.trim()); });
    window._products = products;
  } catch (e) { content().innerHTML = errBanner(e.message); }
}
function productCard(p) {
  const skus = skusOf(p), open = openProduct === p.id;
  return `<div class="card tap" id="pc-${p.id}">
    <div class="row between" onclick="toggleProduct('${p.id}')">
      <div class="grow"><div class="name">${esc(p.title)}</div><div class="small">${esc(skus.map((k) => k.sku_code).join(", ") || "No SKU")}</div></div>
      <div style="text-align:right">${pill(p.status || "DRAFT")}${skus[0] ? `<div class="name num" style="margin-top:6px">${money(skus[0].price)}</div>` : ""}</div>
    </div>
    ${open ? editForm(p, skus) : ""}
  </div>`;
}
function editForm(p, skus) {
  return `<div class="divider">
    <label class="lbl" style="margin-top:0">Product name</label><input id="e-title" value="${esc(p.title)}" />
    <label class="lbl">Status</label>
    <div class="chips wrap" id="e-status" data-v="${esc(p.status)}">${["DRAFT", "ACTIVE", "ARCHIVED"].map((s) => `<button class="chip ${p.status === s ? "on" : ""}" data-s="${s}" onclick="pickStatus(this)">${s}</button>`).join("")}</div>
    ${skus.map((k) => `<label class="lbl">${esc(k.sku_code)} price (₹)</label><input class="e-price" data-id="${k.id}" data-old="${esc(k.price)}" inputmode="decimal" value="${esc(k.price)}" />`).join("")}
    <div id="e-err"></div>
    <div class="row" style="margin-top:14px"><button class="btn grow" style="flex:2" onclick="saveProduct('${p.id}',this)">Save changes</button>
    <button class="btn danger grow" onclick="removeProduct('${p.id}')">Delete</button></div></div>`;
}
function toggleProduct(id) { openProduct = openProduct === id ? null : id; const p = window._products; const el = $("pc-" + id); if (!el) return; renderProducts(prodSearch); }
function pickStatus(b) { const w = $("e-status"); w.dataset.v = b.dataset.s; w.querySelectorAll(".chip").forEach((c) => c.classList.toggle("on", c === b)); }
async function saveProduct(id, btn) {
  const title = $("e-title").value.trim();
  if (!title) { $("e-err").innerHTML = errBanner("Product ka naam khaali nahi ho sakta."); return; }
  await busy(btn, async () => {
    try {
      await api.updateProduct(id, { title, status: $("e-status").dataset.v });
      for (const inp of document.querySelectorAll(".e-price")) if (inp.value !== inp.dataset.old) await api.updateSku(inp.dataset.id, { price: inp.value });
      openProduct = null; toast("Saved"); renderProducts(prodSearch);
    } catch (e) { $("e-err").innerHTML = errBanner(e.message); }
  });
}
function removeProduct(id) {
  const p = (window._products || []).find((x) => x.id === id);
  const o = sheet(`<h3>Product delete karna hai?</h3><div class="small">${esc(p ? p.title : "")}</div>
    <div class="small" style="margin-top:8px">Iski stock history bhi hat jayegi. Jis marketplace par ye laga hai wahan se use khud hatana hoga.</div>
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn quiet" id="d-no">Rehne do</button><button class="btn danger" id="d-yes">Delete</button></div>`);
  o.querySelector("#d-no").onclick = () => o.remove();
  o.querySelector("#d-yes").onclick = (e) => busy(e.target, async () => {
    try { await api.deleteProduct(id); o.remove(); openProduct = null; toast("Deleted"); renderProducts(prodSearch); }
    catch (er) {
      sheetErr(o, er.message);
      if (/ARCHIVED/.test(er.message) && !o.querySelector("#d-arch")) {
        const b = document.createElement("button"); b.className = "btn"; b.id = "d-arch"; b.style.marginTop = "10px"; b.textContent = "Archive karo";
        o.querySelector(".sheet").appendChild(b);
        b.onclick = () => busy(b, async () => {
          try { await api.updateProduct(id, { status: "ARCHIVED" }); o.remove(); openProduct = null; toast("Archive ho gaya"); renderProducts(prodSearch); }
          catch (e2) { sheetErr(o, e2.message); }
        });
      }
    }
  });
}
function showAddProduct() {
  const o = sheet(`<h3>New product</h3>
    <label class="lbl">Product name</label><input id="np-title" placeholder="Cotton shirt" />
    <label class="lbl">SKU code</label><input id="np-sku" autocapitalize="characters" placeholder="SHIRT-BLU-M" /><div class="hint">Har SKU ka code alag hona chahiye.</div>
    <label class="lbl">Price (₹)</label><input id="np-price" inputmode="decimal" placeholder="499" />
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn quiet" id="np-cancel">Cancel</button><button class="btn" id="np-save">Save product</button></div>`);
  o.querySelector("#np-cancel").onclick = () => o.remove();
  o.querySelector("#np-save").onclick = (e) => busy(e.target, async () => {
    const title = o.querySelector("#np-title").value.trim(), skuCode = o.querySelector("#np-sku").value.trim(), price = o.querySelector("#np-price").value;
    if (!title || !skuCode || !price) return sheetErr(o, "Title, SKU code aur price teeno chahiye.");
    try { await api.createProductWithSku({ title, skuCode, price }); o.remove(); toast("Product add ho gaya"); renderProducts(prodSearch); }
    catch (er) { sheetErr(o, er.message); }
  });
}

// ================= Stock =================
async function renderStock() {
  try {
    const [balances, skus] = await Promise.all([api.balances(), api.skus()]);
    skuCache = skus;
    const seen = new Set(balances.map((b) => b.sku_id || b.sku));
    const missing = skus.filter((k) => !seen.has(k.id)).map((k) => ({ sku_id: k.id, sku_code: k.sku_code, on_hand: 0, reserved: 0, available: 0 }));
    balances.push(...missing);
    window._balances = balances;
    setSub(balances.length === 1 ? "1 SKU" : `${balances.length} SKUs`);
    content().innerHTML = balances.length ? balances.map((b) => {
      const id = b.sku_id || b.sku, low = b.available <= 0;
      return `<div class="card tap ${low ? "accent red" : ""}" onclick="showStock('${id}')">
        <div class="row between"><div class="name">${esc(b.sku_code || b.sku)}</div>${low ? pill("FAILED").replace("FAILED", "OUT OF STOCK") : ""}</div>
        <div class="stats"><div><div class="v num">${num(b.available)}</div><div class="l">Available</div></div>
        <div><div class="v num">${num(b.on_hand)}</div><div class="l">On hand</div></div>
        <div><div class="v num">${num(b.reserved)}</div><div class="l">Reserved</div></div></div></div>`;
    }).join("") : empty("Abhi koi stock record nahi", "Product add karo, phir yahan stock daal sakte ho.");
  } catch (e) { content().innerHTML = errBanner(e.message); }
}
async function showStock(id) {
  const b = (window._balances || []).find((x) => (x.sku_id || x.sku) === id) || {};
  const o = sheet(`<h3>${esc(b.sku_code || "Stock")}</h3><div class="small">Available ${num(b.available)} · On hand ${num(b.on_hand)} · Reserved ${num(b.reserved)}</div>
    <label class="lbl">Quantity</label>
    <div class="stepper"><button class="s" id="q-minus">−</button><input id="q-val" inputmode="numeric" value="1" /><button class="s" id="q-plus">+</button></div>
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn danger" id="q-rem">Remove</button><button class="btn" id="q-add">Add</button></div>
    <div class="section">History</div><div id="q-hist" class="small">Loading…</div>`);
  const q = o.querySelector("#q-val");
  const get = () => Math.max(parseInt(q.value, 10) || 0, 0);
  o.querySelector("#q-minus").onclick = () => (q.value = Math.max(get() - 1, 1));
  o.querySelector("#q-plus").onclick = () => (q.value = get() + 1);
  const apply = (sign) => (e) => busy(e.target, async () => {
    const n = get(); if (!n) return sheetErr(o, "Quantity 1 ya usse zyada daalo.");
    try { await api.adjust(id, sign * n); o.remove(); toast(sign > 0 ? `${n} add kiye` : `${n} hata diye`); renderStock(); }
    catch (er) { sheetErr(o, er.message); }
  });
  o.querySelector("#q-add").onclick = apply(1); o.querySelector("#q-rem").onclick = apply(-1);
  try {
    const h = (await api.ledger(id)).slice(0, 8);
    o.querySelector("#q-hist").innerHTML = h.length ? h.map((e) => `<div class="ledger-row"><div><div style="color:var(--ink)">${esc(String(e.entry_type).toLowerCase())}</div><div class="small">${esc(new Date(e.created_at).toLocaleString())}</div></div><div class="delta ${e.quantity_delta > 0 ? "up" : "down"} num">${e.quantity_delta > 0 ? "+" : ""}${num(e.quantity_delta)}</div></div>`).join("") : "Abhi koi history nahi.";
  } catch (er) { o.querySelector("#q-hist").textContent = er.message; }
}

// ================= Orders =================
const NEXT = { IMPORTED: ["Confirm", "confirm"], CONFIRMED: ["Pack", "pack"], PACKED: ["Ship", "ship"], SHIPPED: ["Mark delivered", "deliver"] };
const CANCELLABLE = ["IMPORTED", "CONFIRMED", "PACKED"];
const STATUSES = ["", "IMPORTED", "CONFIRMED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"];
async function renderOrders(filter = "") {
  orderFilter = filter;
  const chips = `<div class="chips">${STATUSES.map((s) => `<button class="chip ${filter === s ? "on" : ""}" onclick="renderOrders('${s}')">${s || "All"}</button>`).join("")}</div>`;
  try {
    const orders = await api.orders(filter);
    setSub(orders.length === 1 ? "1 order" : `${orders.length} orders`);
    content().innerHTML = chips + `<button class="btn" style="margin-top:0;margin-bottom:12px" onclick="showAddOrder()">New order</button>` +
      (orders.length ? orders.map((o) => {
        const next = NEXT[o.status];
        return `<div class="card"><div class="row between"><div class="grow"><div class="name">${esc(o.order_number)}</div><div class="small">${esc(o.customer_name || "Walk-in")}${o.channel_name ? ` · via ${esc(o.channel_name)}` : ""}</div></div>
          <div style="text-align:right">${pill(o.status)}<div class="name num" style="margin-top:6px">${money(o.total_amount)}</div></div></div>
          ${(o.items || []).map((li) => `<div class="small">${esc(li.sku_code)} × ${num(li.quantity)} @ ${money(li.unit_price)}</div>`).join("")}
          ${next || CANCELLABLE.includes(o.status) ? `<div class="row" style="margin-top:12px">
            ${next ? `<button class="btn sm grow" onclick="orderStep('${o.id}','${o.status}',this)">${next[0]}</button>` : ""}
            ${CANCELLABLE.includes(o.status) ? `<button class="btn sm quiet grow" style="color:var(--danger)" onclick="cancelOrder('${o.id}')">Cancel</button>` : ""}</div>` : ""}</div>`;
      }).join("") : empty("Koi order nahi", filter ? "Is status mein abhi koi order nahi." : "Pehla order banake dekho."));
  } catch (e) { content().innerHTML = chips + errBanner(e.message); }
}
async function orderStep(id, status, btn) {
  await busy(btn, async () => {
    try { await api.orderStep(id, NEXT[status][1], status === "PACKED" ? {} : undefined); toast("Order update ho gaya"); renderOrders(orderFilter); }
    catch (e) { toast(e.message, true); }
  });
}
function cancelOrder(id) {
  const o = sheet(`<h3>Order cancel karni hai?</h3><div class="small">Reserved stock wapas available ho jayega.</div>
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn quiet" id="c-no">Rehne do</button><button class="btn danger" id="c-yes">Cancel order</button></div>`);
  o.querySelector("#c-no").onclick = () => o.remove();
  o.querySelector("#c-yes").onclick = (e) => busy(e.target, async () => {
    try { await api.cancelOrder(id, "seller/customer request"); o.remove(); toast("Order cancel ho gaya"); renderOrders(orderFilter); }
    catch (er) { sheetErr(o, er.message); }
  });
}
async function showAddOrder() {
  if (!skuCache.length) { try { skuCache = await api.skus(); } catch {} }
  const o = sheet(`<h3>New order</h3>
    <label class="lbl">Customer name</label><input id="no-name" placeholder="Ramesh Kumar" />
    <label class="lbl">SKU</label>
    <div class="chips" style="margin-bottom:6px">${skuCache.slice(0, 20).map((s) => `<button class="chip" data-c="${esc(s.sku_code)}">${esc(s.sku_code)}</button>`).join("")}</div>
    <input id="no-sku" autocapitalize="characters" placeholder="SKU code" />
    <label class="lbl">Quantity</label><input id="no-qty" inputmode="numeric" value="1" />
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn quiet" id="no-cancel">Cancel</button><button class="btn" id="no-save">Create order</button></div>`);
  o.querySelectorAll(".chip").forEach((c) => (c.onclick = () => { o.querySelector("#no-sku").value = c.dataset.c; o.querySelectorAll(".chip").forEach((x) => x.classList.toggle("on", x === c)); }));
  o.querySelector("#no-cancel").onclick = () => o.remove();
  o.querySelector("#no-save").onclick = (e) => busy(e.target, async () => {
    const name = o.querySelector("#no-name").value.trim(), code = o.querySelector("#no-sku").value.trim().toLowerCase();
    const qty = parseInt(o.querySelector("#no-qty").value, 10) || 1;
    const sku = skuCache.find((s) => s.sku_code.toLowerCase() === code);
    if (!sku) return sheetErr(o, `SKU "${code}" nahi mila. Upar se ek chuno.`);
    try { await api.createOrder({ customer_name: name, items: [{ sku: sku.id, quantity: qty }] }); o.remove(); toast("Order ban gaya"); renderOrders(""); }
    catch (er) { sheetErr(o, er.message); }
  });
}

// ================= More / Channels / Sync =================
async function renderMore() {
  let me = {};
  try { me = await api.me(); } catch {}
  content().innerHTML = `
    <div class="card"><div class="name">${esc(me.email || me.username || "Account")}</div><div class="small">${esc(String(me.role || "").replace("_", " ").toLowerCase())}</div></div>
    <div class="card tap menu-item" onclick="go('channels')"><div><div class="name">Channels</div><div class="small">Shopify, WooCommerce ya Demo store connect karo</div></div><span class="chev">›</span></div>
    <div class="card tap menu-item" onclick="go('sync')"><div><div class="name">Sync</div><div class="small">Product publish karo, jobs dekho</div></div><span class="chev">›</span></div>
    <div class="card tap menu-item" onclick="go('settings')"><div><div class="name">Settings</div><div class="small">Language, App guide, Delete account</div></div><span class="chev">›</span></div>
    <div class="card tap menu-item" onclick="exportCsv('orders')"><div><div class="name">Export orders (CSV)</div><div class="small">Saare channels ke orders ek file mein</div></div><span class="chev">›</span></div>
    <div class="card tap menu-item" onclick="exportCsv('stock')"><div><div class="name">Export stock (CSV)</div><div class="small">SKU wise stock</div></div><span class="chev">›</span></div>
    <button class="btn quiet" style="margin-top:14px" onclick="logout()">Log out</button>`;
}
async function renderSettings() {
  let me = {};
  try { me = await api.me(); } catch {}
  const lang = (window.I18N && I18N.LANGS[I18N.lang]) || "";
  content().innerHTML = `
    <div class="card tap menu-item" onclick="I18N.langSheet()"><div><div class="name">Language</div><div class="small" data-no-i18n>${esc(lang)}</div></div><span class="chev">›</span></div>
    <div class="card tap menu-item" onclick="Tour.start()"><div><div class="name">App guide</div><div class="small">App kaise use karni hai, dobara dekho</div></div><span class="chev">›</span></div>
    <button class="btn quiet" style="margin-top:18px;color:var(--danger)" onclick="showDeleteAccount('${esc(me.role || "")}')">Delete account</button>`;
}
function showDeleteAccount(role) {
  const owner = role === "OWNER";
  const o = sheet(`<h3>Account delete karna hai?</h3>
    <div class="small">${owner ? "Aapka poora store hat jayega: products, stock, orders, channels aur saare users. Ye wapas nahi aayega." : "Aapka login hat jayega. Store ka data rahega."}</div>
    <label class="lbl">Confirm ke liye DELETE likho</label><input id="del-confirm" autocapitalize="characters" />
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn quiet" id="del-no">Rehne do</button><button class="btn danger" id="del-yes">Delete account</button></div>`);
  o.querySelector("#del-no").onclick = () => o.remove();
  o.querySelector("#del-yes").onclick = (e) => busy(e.target, async () => {
    if (o.querySelector("#del-confirm").value.trim() !== "DELETE") return sheetErr(o, "DELETE likhna zaroori hai.");
    try {
      await api.deleteAccount();
      try { if (getFA()) await getFA().deleteUser(); } catch {}
      clearToken(); o.remove(); showLogin(); toast("Account delete ho gaya");
    } catch (er) { sheetErr(o, er.message); }
  });
}

async function renderChannels() {
  try {
    const items = await api.connections();
    content().innerHTML = `<button class="btn" style="margin-top:0" onclick="showConnect()">Connect a channel</button><div style="height:12px"></div>` +
      (items.length ? items.map((i) => `<div class="card"><div class="row between"><div class="grow"><div class="name">${esc(i.name)}</div><div class="small">${esc(i.channel === "DEMO" ? "Demo" : i.channel === "FILE" ? "CSV file" : i.channel === "FLIPKART" ? "Flipkart (Beta)" : i.shop_domain)}</div></div>${pill(i.status)}</div>
        ${i.last_error ? `<div class="err-text">${esc(i.last_error)}</div>` : ""}
        <div class="row" style="margin-top:12px;gap:6px">${["MANUAL:Manual","CONFIRM:Auto confirm","PACK:Auto pack"].map(x => { const [v, l] = x.split(":"); return `<button class="chip ${(i.auto_process || "MANUAL") === v ? "on" : ""}" onclick="setAuto('${i.id}','${v}')">${l}</button>`; }).join("")}</div><div class="small muted" style="margin:6px 0 0">Naya order aate hi: ${{MANUAL: "aap khud confirm/pack karoge", CONFIRM: "apne aap confirm hoga", PACK: "apne aap confirm + pack hoga (ship aap karoge)"}[i.auto_process || "MANUAL"]}</div>${i.channel !== "FILE" ? `<div class="row" style="margin-top:12px;gap:6px"><button class="chip ${i.auto_publish ? "on" : ""}" onclick="setAutoPublish('${i.id}',${!i.auto_publish})">Auto publish ${i.auto_publish ? "ON" : "OFF"}</button><button class="chip" onclick="publishAll('${i.id}',this)">Publish all products</button></div><div class="small muted" style="margin:6px 0 0">${i.auto_publish ? "Naya product ya badlav apne aap is channel par jayega." : "Product aap Sync se khud bhejoge."}</div>` : ""}<div class="row" style="margin-top:12px">${i.channel === "DEMO" && i.status === "CONNECTED" ? `<button class="btn sm grow" onclick="simulate('${i.id}',this)">Test order</button>` : ""}${i.channel === "FILE" ? `<button class="btn sm grow" onclick="importCsv('${i.id}')">Import CSV</button>` : ""}${i.channel !== "DEMO" && i.channel !== "FILE" && i.status === "CONNECTED" ? `<button class="btn sm grow" onclick="pullOrders('${i.id}',this)">Fetch orders</button>` : ""}<button class="btn sm quiet grow" onclick="recheck('${i.id}',this)">Check again</button><button class="btn sm quiet grow" style="color:var(--danger)" onclick="removeConn('${i.id}')">Remove</button></div></div>`).join("")
        : empty("Koi channel connected nahi", "Pehle Demo channel connect karke poora flow try kar sakte ho."));
  } catch (e) { content().innerHTML = errBanner(e.message); }
}
function showConnect() {
  const o = sheet(`<h3>Connect a channel</h3>
    <label class="lbl">Channel</label><div class="chips" id="cn-ch"><button class="chip on" data-v="DEMO">Demo (test)</button><button class="chip" data-v="SHOPIFY">Shopify</button><button class="chip" data-v="WOOCOMMERCE">WooCommerce</button><button class="chip" data-v="FLIPKART">Flipkart (Beta)</button><button class="chip" data-v="FILE">CSV file</button></div>
    <label class="lbl">Name</label><input id="cn-name" placeholder="My Shopify store" />
    <div id="cn-dom-w" class="hidden"><label class="lbl">Store address</label><input id="cn-dom" autocapitalize="none" placeholder="mystore.myshopify.com" /><div class="hint" id="cn-dom-h"></div></div>
    <label class="lbl" id="cn-tok-l">Access token</label><input id="cn-tok" type="password" autocapitalize="none" /><div class="hint" id="cn-hint">Test ke liye "demo" likho.</div>
    <div class="hint hidden" id="cn-file-h">Meesho, Nykaa, Flipkart, Amazon: seller panel se order file (CSV) download karo aur yahan import karo. Channel ka naam wahi rakho (jaise Meesho).</div>
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn quiet" id="cn-cancel">Cancel</button><button class="btn" id="cn-save">Connect</button></div>`);
  let ch = "DEMO";
  o.querySelectorAll("#cn-ch .chip").forEach((c) => (c.onclick = () => {
    ch = c.dataset.v; o.querySelectorAll("#cn-ch .chip").forEach((x) => x.classList.toggle("on", x === c));
    o.querySelector("#cn-dom-w").classList.toggle("hidden", ch === "DEMO" || ch === "FILE" || ch === "FLIPKART");
    ["#cn-tok-l", "#cn-tok", "#cn-hint"].forEach((q) => o.querySelector(q).classList.toggle("hidden", ch === "FILE"));
    o.querySelector("#cn-file-h").classList.toggle("hidden", ch !== "FILE");
    const H = {
      DEMO: ['Access token', 'Test ke liye "demo" likho.', "", ""],
      SHOPIFY: ["Token ya Client ID:Secret", "Purana token (shpat_...) ya naye Dev Dashboard app ka client_id:client_secret. Encrypted save hota hai, wapas nahi dikhta.", "mystore.myshopify.com", ""],
      FLIPKART: ["Application ID:Secret", "Format: application_id:application_secret (Flipkart seller panel > Developer Access). BETA: asli account par test baaki. Naya listing Flipkart panel se banao (SKU wahi rakho), app stock aur orders sambhalega.", "", ""],
      WOOCOMMERCE: ["API keys (key:secret)", "Format: consumer_key:consumer_secret. WooCommerce > Settings > Advanced > REST API se Read/Write key banao.", "mystore.com", "Sirf https wali site, bina https:// ke."],
    }[ch];
    o.querySelector("#cn-tok-l").textContent = H[0]; o.querySelector("#cn-hint").textContent = H[1];
    o.querySelector("#cn-dom").placeholder = H[2]; o.querySelector("#cn-dom-h").textContent = H[3];
  }));
  o.querySelector("#cn-cancel").onclick = () => o.remove();
  o.querySelector("#cn-save").onclick = (e) => busy(e.target, async () => {
    const name = o.querySelector("#cn-name").value.trim(), tok = o.querySelector("#cn-tok").value.trim(), dom = o.querySelector("#cn-dom").value.trim();
    if (!name || (ch !== "FILE" && !tok)) return sheetErr(o, ch === "FILE" ? "Channel ka naam daalo." : "Naam aur token dono daalo.");
    try { await api.createConnection({ channel: ch, name, shop_domain: dom, access_token: tok }); o.remove(); toast("Channel connect ho gaya"); renderChannels(); }
    catch (er) { sheetErr(o, er.message); }
  });
}
async function setAutoPublish(id, on) { try { await api.setAutoPublish(id, on); toast("Setting save ho gayi"); renderChannels(); } catch (e) { toast(e.message, true); } }
async function publishAll(id, btn) {
  await busy(btn, async () => {
    try {
      const r = await api.publishAll(id);
      toast(`${r.queued} products bhejne ke liye lage` + (r.no_sku ? `, ${r.no_sku} bina SKU ke chhoote` : ""));
    } catch (e) { toast(e.message, true); }
  });
}
async function setAuto(id, level) { try { await api.setAuto(id, level); toast("Setting save ho gayi"); renderChannels(); } catch (e) { toast(e.message, true); } }
async function simulate(id, btn) {
  await busy(btn, async () => {
    try { const o = await api.simulateOrder(id); toast(`Nakli order aaya: ${o.order_number}. Orders tab mein dekho.`); }
    catch (e) { toast(e.message, true); }
  });
}
async function pullOrders(id, btn) {
  await busy(btn, async () => {
    try {
      const r = await api.pullOrders(id);
      const f = r.failed || [];
      toast(`${r.new} naye order aaye` + (r.existing ? `, ${r.existing} pehle se the` : "") + (f.length ? `, ${f.length} nahi aa paye` : ""), f.length > 0 && r.new === 0);
      if (f.length) showFailedOrders(f);
      renderChannels();
    } catch (e) { toast(e.message, true); }
  });
}
function showFailedOrders(f) {
  sheet(`<h3>Ye orders nahi aa paye</h3><div class="small">Aksar wajah: SKU catalog mein nahi hai. Wahi SKU code se product banao, phir dobara Import / Fetch karo.</div>
    <div style="max-height:50vh;overflow-y:auto">` + f.map((x) => `<div class="card"><div class="name">${esc(x.order)}</div><div class="err-text">${esc(x.error)}</div></div>`).join("") + `</div>`);
}
function importCsv(connId) {
  const inp = document.createElement("input");
  inp.type = "file"; inp.accept = ".csv,text/csv,text/plain,application/vnd.ms-excel";
  inp.onchange = async () => {
    const file = inp.files && inp.files[0]; if (!file) return;
    if (/\.xlsx?$/i.test(file.name)) return toast("Excel file nahi chalti. Excel mein Save as > CSV karke daalo.", true);
    let rows; try { rows = CsvImport.parse(await file.text()); } catch { return toast("File padh nahi paye.", true); }
    if (rows.length < 2) return toast("File mein koi order row nahi mili.", true);
    showCsvMapping(connId, rows);
  };
  inp.click();
}
function showCsvMapping(connId, rows) {
  const headers = rows[0].map((h, i) => String(h || "").trim() || `Column ${i + 1}`);
  const key = "omnisell_csvmap:" + headers.join("|");
  let map = CsvImport.guess(headers);
  try { const sv = JSON.parse(localStorage.getItem(key) || "null"); if (sv) map = sv; } catch {}
  const opt = (sel) => `<option value="-1">${esc(window.t ? t("— skip —") : "— skip —")}</option>` + headers.map((h, i) => `<option value="${i}" ${sel === i ? "selected" : ""}>${esc(h)}</option>`).join("");
  const o = sheet(`<h3>Columns match karo</h3><div class="small">Har cheez file ke kaunse column mein hai, ye chuno. * zaroori hai.</div>
    <div style="max-height:46vh;overflow-y:auto;margin-top:6px">${CsvImport.FIELDS.map((f) => `<label class="lbl">${f.label}${f.req ? " *" : ""}</label><select class="cm" data-no-i18n data-k="${f.k}">${opt(map[f.k])}</select>`).join("")}</div>
    <div class="small" id="cm-sum" style="margin-top:10px"></div>
    <div class="row sheet-actions" style="margin-top:12px"><button class="btn quiet" id="cm-no">Cancel</button><button class="btn" id="cm-go">Import</button></div>`);
  let built = null;
  const refresh = () => {
    o.querySelectorAll(".cm").forEach((s) => (map[s.dataset.k] = parseInt(s.value, 10)));
    built = CsvImport.build(rows, map);
    const miss = CsvImport.FIELDS.filter((f) => f.req && map[f.k] < 0);
    o.querySelector("#cm-sum").textContent = miss.length ? "Zaroori column chuno: " + miss.map((f) => f.label).join(", ")
      : `${built.orders.length} orders · ${built.lines} lines import honge` + (built.skipped ? ` · ${built.skipped} rows chhoot gayi (khaali ya galat)` : "");
    o.querySelector("#cm-go").disabled = !!miss.length || !built.orders.length;
  };
  o.querySelectorAll(".cm").forEach((s) => (s.onchange = refresh)); refresh();
  o.querySelector("#cm-no").onclick = () => o.remove();
  o.querySelector("#cm-go").onclick = (e) => busy(e.target, async () => {
    try { localStorage.setItem(key, JSON.stringify(map)); } catch {}
    const tot = { new: 0, existing: 0, failed: [] };
    try {
      for (let i = 0; i < built.orders.length; i += 100) {
        const r = await api.importOrders(connId, built.orders.slice(i, i + 100));
        tot.new += r.new; tot.existing += r.existing; tot.failed.push(...(r.failed || []));
      }
    } catch (er) { return sheetErr(o, er.message + (tot.new ? ` (${tot.new} orders aa chuke the)` : "")); }
    o.remove();
    toast(`${tot.new} naye order aaye` + (tot.existing ? `, ${tot.existing} pehle se the` : "") + (tot.failed.length ? `, ${tot.failed.length} nahi aa paye` : ""), tot.failed.length > 0 && tot.new === 0);
    if (tot.failed.length) showFailedOrders(tot.failed);
  });
}
function parseCsv(t) {
  const rows = []; let r = [], f = "", q = false;
  for (let i = 0; i < t.length; i++) {
    const c = t[i];
    if (q) { if (c === '"') { if (t[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"') q = true;
    else if (c === ",") { r.push(f); f = ""; }
    else if (c === "\n") { r.push(f); rows.push(r); r = []; f = ""; }
    else if (c !== "\r") f += c;
  }
  if (f || r.length) { r.push(f); rows.push(r); }
  return rows.filter((x) => x.length > 1);
}
function csvList(kind, rows) {
  const h = rows[0], data = rows.slice(1).map((r) => Object.fromEntries(h.map((k, i) => [k, r[i]])));
  if (!data.length) return empty("Abhi kuch nahi hai", kind === "orders" ? "Order aane par yahan dikhega." : "Stock add karne par yahan dikhega.");
  if (kind === "stock") {
    const total = data.reduce((n, x) => n + (+x.available || 0), 0);
    return `<div class="small" style="margin:4px 0 10px">${data.length} SKU · kul available ${total}</div>` + data.map((x) =>
      `<div class="card"><div class="row between"><div class="grow"><div class="name">${esc(x.sku)}</div><div class="small">${esc(x.product)} · ${money(x.price)}</div></div>
      <div style="text-align:right"><div class="name num">${esc(x.available)}</div><div class="small">${esc(x.on_hand)} haath mein · ${esc(x.reserved)} reserved</div></div></div></div>`).join("");
  }
  const by = new Map();
  data.forEach((x) => { if (!by.has(x.order_number)) by.set(x.order_number, { ...x, lines: [] }); by.get(x.order_number).lines.push(x); });
  const orders = [...by.values()];
  const sum = orders.reduce((n, o) => n + o.lines.reduce((m, l) => m + (+l.line_total || 0), 0), 0);
  return `<div class="small" style="margin:4px 0 10px">${orders.length} orders · kul ${money(sum)}</div>` + orders.map((o) =>
    `<div class="card"><div class="row between"><div class="grow"><div class="name">${esc(o.order_number)}</div><div class="small">${esc(o.customer_name || "—")}${o.city ? " · " + esc(o.city) : ""}</div><div class="small">${esc(o.channel)} · ${esc(o.date)}</div></div>
    <div style="text-align:right">${pill(o.status)}<div class="name num" style="margin-top:6px">${money(o.lines.reduce((m, l) => m + (+l.line_total || 0), 0))}</div></div></div>
    <div class="small" style="margin-top:8px">${o.lines.map((l) => `${esc(l.sku)} × ${esc(l.quantity)}`).join(", ")}</div></div>`).join("");
}
async function exportCsv(kind) {
  try {
    const res = await fetch(`${BASE}/export/${kind}.csv`, { headers: { Authorization: `Token ${getToken()}` } });
    if (!res.ok) throw new Error("Export nahi ho paya (HTTP " + res.status + ").");
    const text = await res.text();
    const o = sheet(`<h3>${kind === "orders" ? "Orders" : "Stock"}</h3>
      <div style="max-height:52vh;overflow-y:auto;margin:0 -4px;padding:0 4px">${csvList(kind, parseCsv(text))}</div>
      <div class="row sheet-actions" style="margin-top:14px"><button class="btn quiet" id="csv-copy">Copy CSV</button><button class="btn" id="csv-share">Share file</button></div>`);
    o.querySelector("#csv-copy").onclick = async () => {
      try { await navigator.clipboard.writeText(text); toast("Copy ho gaya. Sheets / Excel mein paste karo."); }
      catch { toast("Copy nahi hua. Share file use karo.", true); }
    };
    o.querySelector("#csv-share").onclick = async () => {
      try {
        const f = new File([text], `${kind}.csv`, { type: "text/csv" });
        if (navigator.canShare && navigator.canShare({ files: [f] })) await navigator.share({ files: [f], title: `${kind}.csv` });
        else await navigator.share({ title: `${kind}.csv`, text });
      } catch { toast("Share nahi hua. Copy use karo.", true); }
    };
  } catch (e) { toast(e.message, true); }
}
async function recheck(id, btn) { await busy(btn, async () => { try { await api.checkConnection(id); renderChannels(); } catch (e) { toast(e.message, true); } }); }
function removeConn(id) {
  const o = sheet(`<h3>Channel hataana hai?</h3><div class="small">Iske listings aur jobs bhi hat sakte hain.</div>
    <div class="row sheet-actions" style="margin-top:16px"><button class="btn quiet" id="r-no">Rehne do</button><button class="btn danger" id="r-yes">Hatao</button></div>`);
  o.querySelector("#r-no").onclick = () => o.remove();
  o.querySelector("#r-yes").onclick = (e) => busy(e.target, async () => { try { await api.deleteConnection(id); o.remove(); renderChannels(); } catch (er) { sheetErr(o, er.message); } });
}

let syncConn = null, syncProd = null;
async function renderSync() {
  try {
    const [cn, products, listings, jobs] = await Promise.all([api.connections(), api.products(), api.listings(), api.jobs()]);
    const conns = cn.filter((x) => x.status === "CONNECTED");
    const pending = jobs.filter((j) => j.status === "PENDING").length;
    content().innerHTML = `<div class="card">
      <label class="lbl" style="margin-top:0">Channel</label>
      ${conns.length ? `<div class="chips wrap">${conns.map((x) => `<button class="chip ${syncConn === x.id ? "on" : ""}" onclick="syncConn='${x.id}';renderSync()">${esc(x.name)}</button>`).join("")}</div>` : `<div class="small">Pehle More › Channels mein koi channel connect karo.</div>`}
      <label class="lbl">Product</label>
      ${products.length ? `<div class="chips wrap">${products.map((x) => `<button class="chip ${syncProd === x.id ? "on" : ""}" onclick="syncProd='${x.id}';renderSync()">${esc(x.title)}</button>`).join("")}</div>` : `<div class="small">Abhi koi product nahi.</div>`}
      <button class="btn" ${syncConn && syncProd ? "" : "disabled"} onclick="doPublish(this)">Publish</button></div>
      <div class="section">Listings</div>
      ${listings.length ? listings.map((l) => `<div class="card ${l.status === "FAILED" || l.status === "NEEDS_ACTION" ? "accent " + (l.status === "FAILED" ? "red" : "") : ""}"><div class="row between"><div class="grow"><div class="name">${esc(l.product_title)}</div><div class="small">${esc(l.connection_name)}</div></div>${pill(l.status)}</div>${l.last_error ? `<div class="err-text">${esc(l.last_error)}</div>` : ""}</div>`).join("") : empty("Abhi kuch publish nahi hua", "Upar se channel aur product chuno.")}
      <div class="section">Activity</div>
      ${pending ? `<div class="banner warn">${pending} job wait kar rahe hain. Worker chal raha hai? (python manage.py run_sync_worker)</div>` : ""}
      ${jobs.length ? jobs.map((j) => `<div class="card"><div class="row between"><div class="grow"><div>${j.job_type === "PUBLISH_PRODUCT" ? "Publish" : "Stock update"} · ${esc(j.product_title)}${j.sku_code ? ` (${esc(j.sku_code)})` : ""}</div><div class="small">${esc(j.connection_name)} · try ${j.attempts}/${j.max_attempts}</div></div>${pill(j.status)}</div>
        ${j.last_error ? `<div class="err-text">${esc(j.last_error)}</div>` : ""}
        ${j.status === "FAILED" || j.status === "NEEDS_ACTION" ? `<button class="btn sm quiet" style="margin-top:10px" onclick="doRetry('${j.id}',this)">Try again</button>` : ""}</div>`).join("") : empty("Abhi koi activity nahi")}`;
  } catch (e) { content().innerHTML = errBanner(e.message); }
}
async function doPublish(btn) {
  await busy(btn, async () => {
    try { await api.publish(syncProd, syncConn); toast("Publish queue mein gaya. Worker chalte hi ho jayega."); renderSync(); }
    catch (e) { toast(e.message, true); }
  });
}
async function doRetry(id, btn) { await busy(btn, async () => { try { await api.retryJob(id); renderSync(); } catch (e) { toast(e.message, true); } }); }

checkAuth();
