"""Turning a cart into an order.

Two rules this module exists to enforce:

1. Line prices are read from the database at checkout time. Nothing about the
   money on an order comes from the request body.
2. Stock is reserved with a conditional UPDATE inside a transaction, so two
   simultaneous checkouts cannot both buy the last unit.
"""

from __future__ import annotations

from django.db import transaction
from django.db.models import F

from brand.models.order import Order, OrderItem
from brand.models.product import Product
from brand.services.cart import Cart


class CheckoutError(Exception):
    """Checkout could not complete. The message is safe to show a shopper."""


@transaction.atomic
def place_order(*, customer_id: int, cart: Cart, address: str, phone: str) -> Order:
    address = (address or "").strip()
    phone = (phone or "").strip()
    if not address:
        raise CheckoutError("A delivery address is required.")
    if not phone:
        raise CheckoutError("A contact phone number is required.")

    requested = {int(k): v for k, v in cart.raw.items() if str(k).isdigit()}
    if not requested:
        raise CheckoutError("Your cart is empty.")

    # select_for_update keeps the rows stable for the length of the transaction
    # on backends that support it; the conditional UPDATE below is the real
    # guard, so SQLite (which ignores the hint) is still correct.
    products = {
        product.id: product
        for product in Product.objects.select_for_update().filter(id__in=requested)
    }
    missing = set(requested) - set(products)
    if missing:
        raise CheckoutError("A product in your cart is no longer available.")

    order = Order.objects.create(
        customer_id=customer_id, address=address, phone=phone, total_amount=0
    )

    items: list[OrderItem] = []
    total = 0
    for product_id, quantity in sorted(requested.items()):
        product = products[product_id]
        if quantity < 1:
            raise CheckoutError("Cart quantities must be at least 1.")
        reserved = Product.objects.filter(id=product_id, stock__gte=quantity).update(
            stock=F("stock") - quantity
        )
        if not reserved:
            raise CheckoutError(f"Only {product.stock} of {product.name} left in stock.")
        # Price is taken from the row we just locked, never from the request.
        items.append(
            OrderItem(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
            )
        )
        total += product.price * quantity

    OrderItem.objects.bulk_create(items)
    order.total_amount = total
    order.save(update_fields=["total_amount"])
    cart.clear()
    return order
