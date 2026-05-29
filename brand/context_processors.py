"""Template context available on every page."""

from brand.services.accounts import current_customer_id
from brand.services.cart import Cart


def storefront(request):
    """Expose the cart badge count and sign-in state to the base layout."""
    try:
        cart_count = Cart(request.session).item_count
    except AttributeError:  # no session (e.g. a bare RequestFactory request)
        cart_count = 0
    return {
        "cart_item_count": cart_count,
        "is_signed_in": current_customer_id(request) is not None,
    }
