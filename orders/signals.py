"""
orders/signals.py

This is the heart of the real-time system.

How it works:
  1. A client calls POST/PATCH/DELETE on the REST API.
  2. The view calls Order.save() or Order.delete().
  3. Django ORM automatically fires post_save or post_delete signals.
  4. Our receivers below catch those signals.
  5. We call channel_layer.group_send() to push the update to Redis.
  6. Redis delivers the message to all connected WebSocket consumers.
  7. Each consumer forwards the message to its connected browser client.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Order
from .serializers import serialize_order

# The group name all WebSocket clients subscribe to
ORDERS_GROUP = "orders_updates"


def _broadcast(change_type: str, order: Order) -> None:
    """
    Helper that pushes an order change event to the Redis channel layer.
    'type' must match the consumer method name (underscores replace dots).
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        ORDERS_GROUP,
        {
            "type":        "send_order_update",   # → OrderConsumer.send_order_update()
            "change_type": change_type,
            "order":       serialize_order(order),
        }
    )


@receiver(post_save, sender=Order)
def order_saved(sender, instance: Order, created: bool, **kwargs) -> None:
    """
    Fires after every Order.save().
    - created=True  → new order was inserted  (INSERT)
    - created=False → existing order was updated (UPDATE)
    """
    change_type = "INSERT" if created else "UPDATE"
    _broadcast(change_type, instance)


@receiver(post_delete, sender=Order)
def order_deleted(sender, instance: Order, **kwargs) -> None:
    """
    Fires after every Order.delete().
    Note: instance still has its data even after deletion.
    """
    _broadcast("DELETE", instance)
