"""Product copywriting behind a provider interface.

The storefront wants short marketing blurbs for products whose `desc` is empty.
`LocalCopywriter` produces one deterministically with no network access, so the
whole repo — tests included — runs with no API key. Set
``COPYWRITER_BACKEND=anthropic`` to swap in a real model.
"""

from .base import Copywriter, ProductBrief
from .registry import get_copywriter

__all__ = ["Copywriter", "ProductBrief", "get_copywriter"]
