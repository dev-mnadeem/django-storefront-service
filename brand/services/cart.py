"""The cart.

The cart is a dict of ``{"<product id>": quantity}`` kept in the session. This
module is the only code allowed to read or write that dict, so its shape is
pinned in one place and templates never do arithmetic.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from brand.models.product import Product

SESSION_KEY = "cart"


@dataclass(frozen=True)
class CartLine:
    product: Product
    quantity: int

    @property
    def line_total(self) -> int:
        return self.product.price * self.quantity


@dataclass(frozen=True)
class CartView:
    lines: list[CartLine]
    total: int
    item_count: int

    @property
    def is_empty(self) -> bool:
        return not self.lines


class Cart:
    """A session-backed cart."""

    def __init__(self, session) -> None:
        self._session = session
        if not isinstance(session.get(SESSION_KEY), dict):
            session[SESSION_KEY] = {}

    @property
    def raw(self) -> dict[str, int]:
        return self._session[SESSION_KEY]

    def _save(self) -> None:
        self._session[SESSION_KEY] = self.raw
        self._session.modified = True

    def quantity_of(self, product_id) -> int:
        return self.raw.get(str(product_id), 0)

    def add(self, product_id, delta: int = 1) -> int:
        """Change a line by `delta` units and return the new quantity.

        Quantity is clamped to [0, CART_MAX_QUANTITY_PER_LINE]; reaching 0
        removes the line entirely so empty lines never linger in the session.
        """
        key = str(product_id)
        ceiling = settings.CART_MAX_QUANTITY_PER_LINE
        new_quantity = min(self.raw.get(key, 0) + delta, ceiling)
        if new_quantity <= 0:
            self.raw.pop(key, None)
            new_quantity = 0
        else:
            self.raw[key] = new_quantity
        self._save()
        return new_quantity

    def remove_one(self, product_id) -> int:
        return self.add(product_id, delta=-1)

    def discard(self, product_id) -> None:
        self.raw.pop(str(product_id), None)
        self._save()

    def clear(self) -> None:
        self._session[SESSION_KEY] = {}
        self._session.modified = True

    @property
    def item_count(self) -> int:
        return sum(self.raw.values())

    def contents(self) -> CartView:
        """Resolve the cart to products in a single query.

        Ids whose product no longer exists are dropped from the session, so a
        deleted product cannot wedge the cart page.
        """
        ids = [key for key in self.raw if key.isdigit()]
        products = {
            str(product.id): product
            for product in Product.objects.with_category().filter(id__in=ids)
        }
        stale = set(self.raw) - set(products)
        if stale:
            for key in stale:
                self.raw.pop(key, None)
            self._save()

        lines = [
            CartLine(product=products[key], quantity=self.raw[key])
            for key in sorted(products, key=lambda k: products[k].name)
        ]
        return CartView(
            lines=lines,
            total=sum(line.line_total for line in lines),
            item_count=sum(line.quantity for line in lines),
        )
