// ---------- API client ----------
function getToken() { return localStorage.getItem("omnisell_token"); }
function saveToken(t) { localStorage.setItem("omnisell_token", t); }
function clearToken() { localStorage.removeItem("omnisell_token"); }

async function req(path, opts = {}) {
  const token = getToken();
  const res = await fetch(API_URL + "/api/v1" + path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Token ${token}` } : {}),
    },
  });
  const text = await res.text();
  let data = {};
  try { data = JSON.parse(text); } catch {}
  if (!res.ok) throw new Error(data.error || data.detail || `HTTP ${res.status}: ${text.slice(0, 200)}`);
  return data;
}
const list = (d) => (Array.isArray(d) ? d : d.results || []);
const post = (path, body) => req(path, { method: "POST", body: body ? JSON.stringify(body) : undefined });
const patch = (path, body) => req(path, { method: "PATCH", body: JSON.stringify(body) });

const api = {
  login: (username, password) => post("/auth/login", { username, password }),
  me: () => req("/auth/me"),
  dashboard: () => req("/dashboard"),

  products: (search = "") => list(req("/products" + (search ? `?search=${encodeURIComponent(search)}` : ""))),
  getProducts: async (search = "") => list(await req("/products" + (search ? `?search=${encodeURIComponent(search)}` : ""))),
  createProductWithSku: async ({ title, skuCode, price }) => {
    const p = await post("/products", { title, status: "DRAFT" });
    const v = await post("/variants", { product: p.id, name: "Default" });
    return post("/skus", { variant: v.id, sku_code: skuCode, price });
  },
  getSkus: async () => list(await req("/skus")),

  getBalances: async () => list(await req("/inventory/")),
  adjustStock: (sku, delta, reason = "capacitor app") =>
    post("/inventory/adjust", { sku, entry_type: "ADJUSTMENT", quantity_delta: delta, reason,
      idempotency_key: `${sku}-${Date.now()}` }),

  getOrders: async (status = "") => list(await req("/orders" + (status ? `?status=${status}` : ""))),
  createOrder: (body) => post("/orders", { ...body, idempotency_key: `cap-${Date.now()}` }),
  confirmOrder: (id) => post(`/orders/${id}/confirm`),
  packOrder: (id) => post(`/orders/${id}/pack`),
  shipOrder: (id, body) => post(`/orders/${id}/ship`, body || {}),
  deliverOrder: (id) => post(`/orders/${id}/deliver`),
  cancelOrder: (id, reason) => post(`/orders/${id}/cancel`, { reason }),
};

// ---------- App state ----------
let currentTab = "home";
let skuCache = [];

function el(html) { const d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstChild; }
function money(n) { return "₹" + Number(n || 0).toFixed(2); }

// ---------- Login ----------
async function doLogin() {
  const username = document.getElementById("login-username").value.trim();
  const password = document.getElementById("login-password").value;
  const errBox = document.getElementById("login-err");
  errBox.classList.add("hidden");
  try {
    const r = await api.login(username, password);
    saveToken(r.token);
    showApp();
  } catch (e) {
    errBox.textContent = e.message;
    errBox.classList.remove("hidden");
  }
}

async function checkAuth() {
  const token = getToken();
  if (!token) return showLogin();
  try { await api.me(); showApp(); }
  catch { clearToken(); showLogin(); }
}

function showLogin() {
  document.getElementById("login-screen").classList.remove("hidden");
  document.getElementById("app-screen").classList.add("hidden");
}
function showApp() {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("app-screen").classList.remove("hidden");
  go("home");
}
function logout() { clearToken(); showLogin(); }

// ---------- Tab navigation ----------
function go(tab) {
  currentTab = tab;
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("on", t.dataset.tab === tab));
  const titles = { home: "Home", products: "Products", stock: "Stock", orders: "Orders", more: "More" };
  document.getElementById("topbar-title").textContent = titles[tab];
  const content = document.getElementById("content");
  content.innerHTML = `<div class="empty">Loading...</div>`;
  if (tab === "home") renderHome();
  else if (tab === "products") renderProducts();
  else if (tab === "stock") renderStock();
  else if (tab === "orders") renderOrders("");
  else renderMore();
}

// ---------- Home ----------
async function renderHome() {
  const content = document.getElementById("content");
  try {
    const d = await api.dashboard();
    content.innerHTML = `
      <div class="tiles">
        <div class="tile"><div class="num">${d.products_count ?? "-"}</div><div class="lbl">Products</div></div>
        <div class="tile"><div class="num">${d.orders_count ?? "-"}</div><div class="lbl">Orders</div></div>
        <div class="tile"><div class="num">${d.low_stock_count ?? "-"}</div><div class="lbl">Low stock</div></div>
        <div class="tile"><div class="num">${d.pending_orders_count ?? "-"}</div><div class="lbl">Pending orders</div></div>
      </div>`;
  } catch (e) {
    content.innerHTML = `<div class="err-box">${e.message}</div>`;
  }
}

// ---------- Products ----------
async function renderProducts() {
  const content = document.getElementById("content");
  try {
    const [products, skus] = await Promise.all([api.getProducts(), api.getSkus()]);
    skuCache = skus;
    const bySkuProduct = {};
    skus.forEach((s) => { bySkuProduct[s.id] = s; });
    content.innerHTML = products.length
      ? products.map((p) => {
          const theseSkus = skus.filter((s) => s.product === p.id || s.variant_product === p.id);
          return `<div class="card">
            <div class="name">${p.title}</div>
            <div class="sub">${p.status || "DRAFT"}${theseSkus.length ? " • " + theseSkus.map((s) => `${s.sku_code} (${money(s.price)})`).join(", ") : ""}</div>
          </div>`;
        }).join("")
      : `<div class="empty">Koi product nahi. Niche + se add karo.</div>`;
    content.appendChild(el(`<div style="height:16px"></div>`));
  } catch (e) {
    content.innerHTML = `<div class="err-box">${e.message}</div>`;
  }
  addFab(() => showAddProductModal());
}

function showAddProductModal() {
  const overlay = el(`<div class="modal-overlay">
    <div class="modal-sheet">
      <h3>New product</h3>
      <div class="field-label">Title</div><input id="np-title" />
      <div class="field-label">SKU code</div><input id="np-sku" autocapitalize="characters" />
      <div class="field-label">Price</div><input id="np-price" type="number" />
      <div id="np-err" class="err-box hidden"></div>
      <div class="btn-row" style="margin-top:14px">
        <button class="btn secondary" id="np-cancel">Cancel</button>
        <button class="btn" id="np-save">Save</button>
      </div>
    </div>
  </div>`);
  document.body.appendChild(overlay);
  overlay.querySelector("#np-cancel").onclick = () => overlay.remove();
  overlay.querySelector("#np-save").onclick = async () => {
    const title = overlay.querySelector("#np-title").value.trim();
    const skuCode = overlay.querySelector("#np-sku").value.trim();
    const price = overlay.querySelector("#np-price").value;
    try {
      await api.createProductWithSku({ title, skuCode, price });
      overlay.remove();
      renderProducts();
    } catch (e) {
      const err = overlay.querySelector("#np-err");
      err.textContent = e.message;
      err.classList.remove("hidden");
    }
  };
}

// ---------- Stock ----------
async function renderStock() {
  const content = document.getElementById("content");
  try {
    const balances = await api.getBalances();
    content.innerHTML = balances.length
      ? balances.map((b) => `<div class="card">
          <div class="name">${b.sku_code || b.sku}</div>
          <div class="sub">On hand: ${b.on_hand} • Reserved: ${b.reserved} • Available: ${b.available}</div>
          <div class="row">
            <button class="btn secondary" style="flex:1" onclick="adjustPrompt('${b.sku_id || b.sku}', ${b.on_hand})">Adjust</button>
          </div>
        </div>`).join("")
      : `<div class="empty">Koi stock record nahi.</div>`;
  } catch (e) {
    content.innerHTML = `<div class="err-box">${e.message}</div>`;
  }
}

async function adjustPrompt(skuId) {
  const val = prompt("Kitna add/remove karna hai? (negative number ghataane ke liye)");
  if (val === null || val.trim() === "") return;
  const delta = parseInt(val, 10);
  if (isNaN(delta)) return alert("Valid number daalo.");
  try { await api.adjustStock(skuId, delta); renderStock(); }
  catch (e) { alert(e.message); }
}

// ---------- Orders ----------
const NEXT_ACTION = {
  IMPORTED: { label: "Confirm", fn: api.confirmOrder },
  CONFIRMED: { label: "Pack", fn: api.packOrder },
  PACKED: { label: "Ship", fn: (id) => api.shipOrder(id, {}) },
  SHIPPED: { label: "Mark Delivered", fn: api.deliverOrder },
};
const CANCELLABLE = new Set(["IMPORTED", "CONFIRMED", "PACKED"]);
const STATUSES = ["", "IMPORTED", "CONFIRMED", "PACKED", "SHIPPED", "DELIVERED", "CANCELLED"];

async function renderOrders(filter) {
  const content = document.getElementById("content");
  const pills = `<div class="pill-tabs">${STATUSES.map((s) =>
    `<div class="pill ${filter === s ? "on" : ""}" onclick="renderOrders('${s}')">${s || "ALL"}</div>`).join("")}</div>`;
  content.innerHTML = pills + `<div class="empty">Loading...</div>`;
  try {
    const orders = await api.getOrders(filter);
    const body = orders.length
      ? orders.map((o) => {
          const next = NEXT_ACTION[o.status];
          const items = (o.items || []).map((li) =>
            `<div class="sub">&nbsp;&nbsp;${li.sku_code} x${li.quantity} @ ${money(li.unit_price)}</div>`).join("");
          return `<div class="card">
            <div class="name">${o.order_number} — ${o.customer_name || "—"}</div>
            <div class="sub">${o.status} • ${money(o.total_amount)}</div>
            ${items}
            <div class="row">
              ${next ? `<button class="btn" style="flex:1" onclick="orderAction('${o.id}','${o.status}')">${next.label}</button>` : ""}
              ${CANCELLABLE.has(o.status) ? `<button class="btn danger" style="flex:1" onclick="cancelOrderPrompt('${o.id}')">Cancel</button>` : ""}
            </div>
          </div>`;
        }).join("")
      : `<div class="empty">Koi order nahi.</div>`;
    content.innerHTML = pills + body;
  } catch (e) {
    content.innerHTML = pills + `<div class="err-box">${e.message}</div>`;
  }
  addFab(() => showAddOrderModal());
}

async function orderAction(id, status) {
  try { await NEXT_ACTION[status].fn(id); renderOrders(""); }
  catch (e) { alert(e.message); }
}
async function cancelOrderPrompt(id) {
  if (!confirm("Order cancel karni hai?")) return;
  try { await api.cancelOrder(id, "seller/customer request"); renderOrders(""); }
  catch (e) { alert(e.message); }
}

async function showAddOrderModal() {
  if (!skuCache.length) { try { skuCache = await api.getSkus(); } catch {} }
  const overlay = el(`<div class="modal-overlay">
    <div class="modal-sheet">
      <h3>New order</h3>
      <div class="field-label">Customer name</div><input id="no-name" />
      <div class="field-label">SKU code</div><input id="no-sku" autocapitalize="characters" />
      <div class="field-label">Quantity</div><input id="no-qty" type="number" value="1" />
      <div id="no-err" class="err-box hidden"></div>
      <div class="btn-row" style="margin-top:14px">
        <button class="btn secondary" id="no-cancel">Cancel</button>
        <button class="btn" id="no-save">Create</button>
      </div>
    </div>
  </div>`);
  document.body.appendChild(overlay);
  overlay.querySelector("#no-cancel").onclick = () => overlay.remove();
  overlay.querySelector("#no-save").onclick = async () => {
    const customer_name = overlay.querySelector("#no-name").value.trim();
    const skuCode = overlay.querySelector("#no-sku").value.trim().toLowerCase();
    const qty = parseInt(overlay.querySelector("#no-qty").value, 10) || 1;
    const sku = skuCache.find((s) => s.sku_code.toLowerCase() === skuCode);
    const err = overlay.querySelector("#no-err");
    if (!sku) { err.textContent = `SKU "${skuCode}" nahi mila.`; err.classList.remove("hidden"); return; }
    try {
      await api.createOrder({ customer_name, items: [{ sku: sku.id, quantity: qty }] });
      overlay.remove();
      renderOrders("");
    } catch (e) { err.textContent = e.message; err.classList.remove("hidden"); }
  };
}

// ---------- More ----------
function renderMore() {
  const content = document.getElementById("content");
  content.innerHTML = `
    <div class="card"><div class="name">Account</div><div class="sub">Logged in</div></div>
    <button class="btn danger" onclick="logout()">Logout</button>`;
}

// ---------- Floating add button ----------
function addFab(onClick) {
  const old = document.querySelector(".fab");
  if (old) old.remove();
  const fab = el(`<button class="fab">+</button>`);
  fab.onclick = onClick;
  document.body.appendChild(fab);
}

// On tab change away from products/orders, remove fab
const originalGo = go;
go = function (tab) {
  if (tab !== "products" && tab !== "orders") {
    const old = document.querySelector(".fab");
    if (old) old.remove();
  }
  originalGo(tab);
};

checkAuth();
