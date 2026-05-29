"""Presentation-only filters.

Cart arithmetic used to live here (one O(n) scan of the cart per product per
filter call). It now lives in `brand.services.cart`; what remains is formatting.
"""

from django import template
from django.conf import settings

register = template.Library()


@register.filter(name="currency")
def currency(amount) -> str:
    """Render a whole-unit price with the configured prefix."""
    try:
        return f"{settings.STOREFRONT_CURRENCY_PREFIX}{int(amount):,}"
    except (TypeError, ValueError):
        return f"{settings.STOREFRONT_CURRENCY_PREFIX}0"


@register.filter(name="cart_quantity")
def cart_quantity(product, quantities) -> int:
    """Units of `product` in the cart, via a dict lookup rather than a scan."""
    if not quantities:
        return 0
    return quantities.get(str(product.id), 0)
