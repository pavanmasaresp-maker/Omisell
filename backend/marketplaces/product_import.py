"""Store ke maujooda products OmniSell mein laao (SKU, price, stock ke saath)."""
import re
from decimal import Decimal, InvalidOperation

from django.db import transaction

from catalog.models import SKU, Product, Variant
from inventory.services import apply_entry

from .adapters.registry import get_adapter
from .models import ChannelListing


def _price(v):
    try:
        d = Decimal(str(v))
        return d if d >= 0 else Decimal("0")
    except (InvalidOperation, ValueError):
        return Decimal("0")


def import_products(conn, user=None):
    """Returns {"new": n_products, "existing": n_already, "skipped_no_sku": n_variants, "failed": [..]}.
    Pehle se maujood SKU dobara nahi banta (dobara import safe hai). Naye product par
    listing 'ACTIVE' ban jaati hai taaki baad mein publish karne par duplicate na bane."""
    products = get_adapter(conn).fetch_products()
    res = {"new": 0, "existing": 0, "skipped_no_sku": 0, "failed": []}
    tid = conn.tenant_id
    for p in products:
        try:
            with transaction.atomic():
                seen, variants = set(), []
                for v in p["variants"]:
                    code = re.sub(r"\s+", " ", v["sku_code"]).strip()[:100]
                    if not code:
                        res["skipped_no_sku"] += 1
                    elif code not in seen:
                        seen.add(code)
                        variants.append({**v, "sku_code": code})
                if not variants:
                    continue
                have = set(SKU.objects.filter(tenant_id=tid, sku_code__in=seen).values_list("sku_code", flat=True))
                new_vs = [v for v in variants if v["sku_code"] not in have]
                if not new_vs:
                    res["existing"] += 1
                    continue
                prod = Product.objects.create(tenant_id=tid, title=(p["title"] or new_vs[0]["sku_code"])[:300],
                                              description=p.get("description", ""), status=p["status"])
                ChannelListing.objects.get_or_create(
                    connection=conn, product=prod,
                    defaults={"tenant_id": tid, "external_product_id": str(p["external_id"]),
                              "status": ChannelListing.Status.ACTIVE})
                for v in new_vs:
                    var = Variant.objects.create(tenant_id=tid, product=prod, name=(v.get("name") or "Default")[:200])
                    sku = SKU(tenant_id=tid, variant=var, sku_code=v["sku_code"], price=_price(v["price"]))
                    sku._skip_publish = True
                    sku.save()
                    q = int(v.get("quantity") or 0)
                    if q > 0:
                        apply_entry(tenant_id=tid, sku=sku, entry_type="ADJUSTMENT", delta=q,
                                    reason=f"Import from {conn.name}",
                                    idempotency_key=f"import:{conn.id}:{sku.id}", user=user, sync=False)
                res["new"] += 1
        except Exception as e:  # ek product kharab ho to baaki chalte rahein
            res["failed"].append({"product": (p.get("title") or "")[:80], "error": str(e)[:150]})
    return res
