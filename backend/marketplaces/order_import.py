"""Marketplace se aaya order apne system mein lana. Har adapter (aur Demo simulator) isi function se guzarta hai.
Normalized order:
  {"external_order_id": "...", "customer_name": "...", "customer_phone": "...", "shipping_address": {...},
   "items": [{"sku_code": "...", "quantity": 1, "unit_price": "499.00"}]}
Same external_order_id dobara aaye to duplicate order nahi banta (idempotent)."""
import random

from catalog.models import SKU
from inventory.models import InventoryBalance
from orders.services import OrderError, create_order

DEMO_CUSTOMERS = [("Ramesh Kumar", "9876500001", "Pune"), ("Sunita Devi", "9876500002", "Patna"),
                  ("Arjun Mehta", "9876500003", "Surat"), ("Fatima Khan", "9876500004", "Lucknow"),
                  ("Priya Nair", "9876500005", "Kochi")]


def import_order(conn, data):
    """Returns (order, created). Unknown SKU ya kam stock par OrderError (poora order rollback)."""
    ext = str(data["external_order_id"]).strip()
    if not ext:
        raise OrderError("external_order_id zaroori hai.")
    lines, missing = [], []
    for it in data.get("items", []):
        sku = SKU.objects.filter(tenant_id=conn.tenant_id, sku_code=it["sku_code"]).first()
        if sku is None:
            missing.append(it["sku_code"])
            continue
        lines.append({"sku": sku, "quantity": it["quantity"], "unit_price": it.get("unit_price", sku.price)})
    if missing:
        raise OrderError("Ye SKU hamare catalog mein nahi mile: " + ", ".join(missing))
    return create_order(
        tenant_id=conn.tenant_id, user=None, items=lines,
        customer_name=data.get("customer_name", ""), customer_phone=data.get("customer_phone", ""),
        shipping_address=data.get("shipping_address") or {}, channel_connection=conn,
        external_order_id=ext, idempotency_key=f"import:{conn.id}:{ext}")


def make_demo_order(conn, rng=random):
    """Test ke liye: tenant ke kisi SKU ka nakli marketplace order (stock hone par usi SKU ka)."""
    skus = list(SKU.objects.filter(tenant_id=conn.tenant_id).order_by("sku_code"))
    if not skus:
        raise OrderError("Pehle koi product add karo, tabhi nakli order ban sakta hai.")
    avail = {b.sku_id: b.on_hand - b.reserved
             for b in InventoryBalance.objects.filter(tenant_id=conn.tenant_id)}
    stocked = [s for s in skus if avail.get(s.id, 0) > 0]
    sku = rng.choice(stocked or skus)
    qty = rng.randint(1, max(1, min(2, avail.get(sku.id, 1))))
    name, phone, city = rng.choice(DEMO_CUSTOMERS)
    return {"external_order_id": f"DEMO-{rng.randint(10**7, 10**8 - 1)}", "customer_name": name,
            "customer_phone": phone, "shipping_address": {"city": city},
            "items": [{"sku_code": sku.sku_code, "quantity": qty, "unit_price": str(sku.price)}]}
