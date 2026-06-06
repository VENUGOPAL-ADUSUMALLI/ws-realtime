from django.db import models


class Order(models.Model):
    """
    Represents a customer order.
    Any save() or delete() on this model triggers a Django signal
    which pushes real-time updates to connected WebSocket clients.
    """

    STATUS_PENDING = 'pending'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_SHIPPED,   'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
    ]

    customer_name = models.CharField(max_length=255)
    product_name  = models.CharField(max_length=255)
    status        = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Order #{self.id} — {self.customer_name} ({self.status})"
