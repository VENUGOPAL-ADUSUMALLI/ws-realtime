"""
orders/consumers.py

WebSocket consumer that handles real-time connections from browser clients.

Lifecycle:
  connect()           → client opens ws://host/ws/orders/
                        → joins "orders_updates" Redis group
                        → sends a full snapshot of current orders
  send_order_update() → called by channel layer when a signal fires
                        → forwards the event to the WebSocket client
  disconnect()        → client closes connection
                        → leaves "orders_updates" group
"""

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async

from .models import Order
from .serializers import serialize_order

ORDERS_GROUP = "orders_updates"


class OrderConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        # 1. Join the shared broadcast group
        await self.channel_layer.group_add(ORDERS_GROUP, self.channel_name)
        await self.accept()

        # 2. Send a full snapshot so the client starts with current state
        orders = await sync_to_async(
            lambda: list(Order.objects.all().order_by('-updated_at'))
        )()

        await self.send_json({
            "type":   "SNAPSHOT",
            "orders": [serialize_order(o) for o in orders],
        })

    async def disconnect(self, close_code):
        # Leave the group so this channel no longer receives broadcasts
        await self.channel_layer.group_discard(ORDERS_GROUP, self.channel_name)

    # ------------------------------------------------------------------
    # This method is called by the channel layer when signals.py calls
    # channel_layer.group_send(..., {"type": "send_order_update", ...})
    # The method name must match the "type" value (dots → underscores).
    # ------------------------------------------------------------------
    async def send_order_update(self, event):
        await self.send_json({
            "type":        "ORDER_CHANGE",
            "change_type": event["change_type"],  # INSERT | UPDATE | DELETE
            "order":       event["order"],
        })
