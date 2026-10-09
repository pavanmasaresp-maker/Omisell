import { API_URL } from "./config";
import { getToken } from "./storage";

async function req(path, opts = {}) {
  const token = await getToken();
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
const send = (method) => (path, body) =>
  req(path, { method, body: body ? JSON.stringify(body) : undefined });
const post = send("POST");
const patch = send("PATCH");
const del = send("DELETE");

export const login = (username, password) => post("/auth/login", { username, password });
export const me = () => req("/auth/me");
export const getDashboard = () => req("/dashboard");

export const getProducts = async (search = "") =>
  list(await req("/products" + (search ? `?search=${encodeURIComponent(search)}` : "")));
export const updateProduct = (id, body) => patch(`/products/${id}`, body);
export const deleteProduct = (id) => del(`/products/${id}`);
export const getSkus = async () => list(await req("/skus"));
export const updateSku = (id, body) => patch(`/skus/${id}`, body);

export async function createProductWithSku({ title, skuCode, price }) {
  const p = await post("/products", { title, status: "DRAFT" });
  const v = await post("/variants", { product: p.id, name: "Default" });
  return post("/skus", { variant: v.id, sku_code: skuCode, price });
}

export const getBalances = async () => list(await req("/inventory/"));
export const getLedger = async (sku) => list(await req(`/inventory/ledger?sku=${sku}`));
export const adjustStock = (sku, delta, reason = "mobile app") =>
  post("/inventory/adjust", {
    sku, entry_type: "ADJUSTMENT", quantity_delta: delta, reason,
    idempotency_key: `${sku}-${Date.now()}`,
  });

export const getConnections = async () => list(await req("/channels/connections"));
export const createConnection = (body) => post("/channels/connections", body);
export const checkConnection = (id) => post(`/channels/connections/${id}/check`);
export const deleteConnection = (id) => del(`/channels/connections/${id}`);

export const getOrders = async (status = "") =>
  list(await req("/orders" + (status ? `?status=${status}` : "")));
export const getOrder = (id) => req(`/orders/${id}`);
export const createOrder = (body) => post("/orders", { ...body, idempotency_key: `mob-${Date.now()}` });
export const confirmOrder = (id) => post(`/orders/${id}/confirm`);
export const packOrder = (id) => post(`/orders/${id}/pack`);
export const shipOrder = (id, body) => post(`/orders/${id}/ship`, body);
export const deliverOrder = (id) => post(`/orders/${id}/deliver`);
export const cancelOrder = (id, reason) => post(`/orders/${id}/cancel`, { reason });
export const createReturn = (body) => post("/orders/returns", body);
export const decideReturn = (id, approve) => post(`/orders/returns/${id}/decide`, { approve });

export const getJobs = async () => list(await req("/channels/jobs"));
export const retryJob = (id) => post(`/channels/jobs/${id}/retry`);
export const getListings = async () => list(await req("/channels/listings"));
export const publishProduct = (product, connection) => post("/channels/publish", { product, connection });
