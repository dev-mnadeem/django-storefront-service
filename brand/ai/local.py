"""Deterministic fallback copywriter — no network, no key, no randomness."""

from __future__ import annotations

import hashlib

from .base import MAX_BLURB_LENGTH, Copywriter, ProductBrief

OPENERS = (
    "Everyday {category} that earns its place",
    "Simple {category} built to be used, not admired",
    "Made for people who are hard on their {category}",
    "The {category} pick we keep restocking",
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
