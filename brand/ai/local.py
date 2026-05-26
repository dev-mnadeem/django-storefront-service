"""Deterministic fallback copywriter — no network, no key, no randomness."""

from __future__ import annotations

import hashlib

from .base import MAX_BLURB_LENGTH, Copywriter, ProductBrief

# Category names are plural ("bags") or mass nouns ("footwear"), so no opener
# conjugates a verb against them.
OPENERS = (
    "Everyday {category}, chosen to last",
    "Simple {category}, built to be used rather than admired",
    "Made for people who are hard on their {category}",
    "A {category} pick we keep restocking",
    "Quietly good {category}, priced honestly",
)

CLOSERS = (
    "Yours for {price}.",
    "In stock now at {price}.",
    "{price}, delivered.",
    "Ships today — {price}.",
)


def _index(seed: str, modulus: int) -> int:
    """Stable index derived from the seed, so the same product always reads the same."""
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % modulus


class LocalCopywriter(Copywriter):
    name = "local"

    def write_blurb(self, brief: ProductBrief) -> str:
        seed = f"{brief.name}|{brief.category}|{brief.price}"
        category = (brief.category or "everyday").lower()
        opener = OPENERS[_index(seed, len(OPENERS))].format(category=category)
        closer = CLOSERS[_index(seed + "!", len(CLOSERS))].format(price=brief.display_price)
        blurb = f"{brief.name}. {opener}. {closer}"
        return blurb[:MAX_BLURB_LENGTH]
