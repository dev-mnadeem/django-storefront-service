from django.db import models
from django.utils import timezone

from .customer import Customer
from .product import Product


class OrderStatus(models.TextChoices):
    """Lifecycle of a placed order."""

    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    SHIPPED = "shipped", "Shipped"
    CANCELLED = "cancelled", "Cancelled"


class OrderQuerySet(models.QuerySet):
    def for_customer(self, customer_id: int) -> "OrderQuerySet":
        return self.filter(customer_id=customer_id)

    def with_lines(self) -> "OrderQuerySet":
        """Fetch every line and its product in two extra queries, not 2N."""
        return self.prefetch_related("items__product")


class Order(models.Model):
    """One checkout. Money lives on the lines plus a frozen `total_amount`."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    address = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    placed_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    total_amount = models.PositiveIntegerField(default=0)

    objects = OrderQuerySet.as_manager()

    class Meta:
        ordering = ["-placed_at", "-id"]
        indexes = [models.Index(fields=["customer", "-placed_at"], name="order_cust_date_idx")]

    def __str__(self) -> str:
        return f"Order #{self.pk}"

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items.all())

    def recalculate_total(self) -> int:
        self.total_amount = sum(item.line_total for item in self.items.all())
        return self.total_amount


class OrderItem(models.Model):
    """A single product line inside an order.

    `unit_price` is a copy of the product price at the moment of checkout, so a
    later price change never rewrites order history.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="+")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.PositiveIntegerField()

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["order", "product"], name="unique_product_per_order"
            )
        ]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_id}"

    @property
    def line_total(self) -> int:
        return self.unit_price * self.quantity
