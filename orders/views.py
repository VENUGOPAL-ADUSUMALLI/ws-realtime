"""
orders/views.py

Simple Django class-based views for the REST API.
Each write operation (create/update/delete) calls Order.save() or
Order.delete() which automatically triggers the Django signals
that push real-time updates to WebSocket clients.
"""

import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Order
from .serializers import serialize_order


def json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


@method_decorator(csrf_exempt, name='dispatch')
class OrderListView(View):
    """
    GET  /api/orders/   → list all orders
    POST /api/orders/   → create a new order
    """

    def get(self, request):
        orders = Order.objects.all()   # ordered by -updated_at (see Meta)
        return JsonResponse([serialize_order(o) for o in orders], safe=False)

    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return json_error("Invalid JSON body")

        customer_name = body.get("customer_name", "").strip()
        product_name  = body.get("product_name",  "").strip()

        if not customer_name or not product_name:
            return json_error("customer_name and product_name are required")

        # save() triggers post_save signal → WebSocket broadcast
        order = Order.objects.create(
            customer_name=customer_name,
            product_name=product_name,
        )
        return JsonResponse(serialize_order(order), status=201)


@method_decorator(csrf_exempt, name='dispatch')
class OrderDetailView(View):
    """
    GET    /api/orders/<pk>/  → get a single order
    PATCH  /api/orders/<pk>/  → update order status
    DELETE /api/orders/<pk>/  → delete order
    """

    def _get_order(self, pk):
        try:
            return Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return None

    def get(self, request, pk):
        order = self._get_order(pk)
        if not order:
            return json_error("Order not found", status=404)
        return JsonResponse(serialize_order(order))

    def patch(self, request, pk):
        order = self._get_order(pk)
        if not order:
            return json_error("Order not found", status=404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return json_error("Invalid JSON body")

        new_status = body.get("status", "").strip()
        valid = [Order.STATUS_PENDING, Order.STATUS_SHIPPED, Order.STATUS_DELIVERED]
        if new_status not in valid:
            return json_error(f"status must be one of: {valid}")

        order.status = new_status
        # save() triggers post_save signal → WebSocket broadcast
        order.save()
        return JsonResponse(serialize_order(order))

    def delete(self, request, pk):
        order = self._get_order(pk)
        if not order:
            return json_error("Order not found", status=404)

        # delete() triggers post_delete signal → WebSocket broadcast
        order.delete()
        return JsonResponse({"deleted": True, "id": pk})
