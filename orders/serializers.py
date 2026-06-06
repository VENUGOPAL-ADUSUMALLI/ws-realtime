def serialize_order(order) -> dict:
    """
    Converts an Order model instance into a plain Python dict
    that can be safely serialized to JSON.
    """
    return {
        "id":            order.id,
        "customer_name": order.customer_name,
        "product_name":  order.product_name,
        "status":        order.status,
        "updated_at":    order.updated_at.isoformat(),
    }
