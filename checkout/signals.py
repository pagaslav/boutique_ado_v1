from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderLineItem

# Signal to update the order total when an order line item is created or updated
@receiver(post_save, sender=OrderLineItem)
def update_on_save(sender, instance, created, **kwargs):
    """
    Update the order total when a line item is created or updated.
    """
    instance.order.update_total()

# Signal to update the order total when an order line item is deleted
@receiver(post_delete, sender=OrderLineItem)
def update_on_delete(sender, instance, **kwargs):
    """
    Update the order total when a line item is deleted.
    """
    instance.order.update_total()
