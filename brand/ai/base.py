from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

MAX_BLURB_LENGTH = 200


@dataclass(frozen=True)
class ProductBrief:
    """Everything a copywriter is allowed to see about a product."""

    name: str
    category: str
    price: int
    currency_prefix: str = "Rs. "

    @property
    def display_price(self) -> str:
        return f"{self.currency_prefix}{self.price:,}"


@runtime_checkable
class Copywriter(Protocol):
    """Writes a one-line product blurb of at most MAX_BLURB_LENGTH characters."""

    name: str

    def write_blurb(self, brief: ProductBrief) -> str: ...
