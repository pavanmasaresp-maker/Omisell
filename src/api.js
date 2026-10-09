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
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || data.detail || JSON.stringify(data));
  return data;
}
const list = (d) => (Array.isArray(d) ? d : d.results || []);
const post = (path, body) => req(path, { method: "POST", body: JSON.stringify(body) });

export const login = (username, password) => post("/auth/login", { username, password });
export const me = () => req("/auth/me");
export const getProducts = async () => list(await req("/products"));
export const getSkus = async () => list(await req("/skus"));
export const getBalances = async () => list(await req("/inventory/"));

export async function createProductWithSku({ title, skuCode, price }) {
  const p = await post("/products", { title, status: "DRAFT" });
  const v = await post("/variants", { product: p.id, name: "Default" });
  return post("/skus", { variant: v.id, sku_code: skuCode, price });
}

export const adjustStock = (sku, delta, reason = "mobile app") =>
  post("/inventory/adjust", {
    sku, entry_type: "ADJUSTMENT", quantity_delta: delta, reason,
    idempotency_key: `${sku}-${Date.now()}`,
  });
