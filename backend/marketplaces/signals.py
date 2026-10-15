from django.db.models.signals import post_save
from django.dispatch import receiver

from catalog.models import SKU, Product


@receiver(post_save, sender=SKU)
def sku_saved(sender, instance, created, **kwargs):
    """Naya SKU ya badla hua price: Auto publish wale channels par product dobara bhejo."""
    if getattr(instance, "_skip_publish", False):
        return
    from .sync import auto_publish_product
    auto_publish_product(instance.variant.product, salt=f"{instance.id}:{instance.updated_at.timestamp()}")


@receiver(post_save, sender=Product)
def product_saved(sender, instance, created, **kwargs):
    """Naam / status badla to channel par bhi badlo (naya product SKU aane par hi jayega)."""
    if created:
        return
    from .sync import auto_publish_product
    auto_publish_product(instance)
