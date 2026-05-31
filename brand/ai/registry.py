"""Backend lookup for copywriters — the seam where a new provider plugs in."""

from __future__ import annotations

from django.conf import settings

from .base import Copywriter


def get_copywriter(backend: str | None = None) -> Copywriter:
    """Return the configured copywriter, defaulting to the local one."""
    name = (backend or settings.COPYWRITER_BACKEND or "local").strip().lower()
    if name == "anthropic":
        from .anthropic_provider import AnthropicCopywriter

        return AnthropicCopywriter()
    from .local import LocalCopywriter

    return LocalCopywriter()
