"""Copywriter backed by the Claude API.

Selected with ``COPYWRITER_BACKEND=anthropic``. Any failure — missing SDK,
missing key, network error, refusal — degrades to `LocalCopywriter` rather than
breaking the admin action that called it.
"""

from __future__ import annotations

import logging

from django.conf import settings

from .base import MAX_BLURB_LENGTH, Copywriter, ProductBrief
from .local import LocalCopywriter

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You write product blurbs for a small online storefront. "
    f"Reply with one sentence of at most {MAX_BLURB_LENGTH} characters. "
    "No marketing cliches, no emoji, no quotation marks, no preamble."
)


class AnthropicCopywriter(Copywriter):
    name = "anthropic"

    def __init__(self, api_key: str = "", model: str = "") -> None:
        self._api_key = api_key or settings.ANTHROPIC_API_KEY
        self._model = model or settings.COPYWRITER_MODEL
        self._fallback = LocalCopywriter()

    def write_blurb(self, brief: ProductBrief) -> str:
        try:
            import anthropic
        except ModuleNotFoundError:
            logger.warning("anthropic SDK not installed; using the local copywriter")
            return self._fallback.write_blurb(brief)

        if not self._api_key:
            logger.warning("ANTHROPIC_API_KEY is unset; using the local copywriter")
            return self._fallback.write_blurb(brief)

        client = anthropic.Anthropic(api_key=self._api_key)
        prompt = (
            f"Product: {brief.name}\nCategory: {brief.category}\nPrice: {brief.display_price}"
        )
        try:
            response = client.messages.create(
                model=self._model,
                max_tokens=256,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception:  # noqa: BLE001 - never let copy generation break a page
            logger.exception("Claude call failed; using the local copywriter")
            return self._fallback.write_blurb(brief)

        if response.stop_reason == "refusal":
            logger.warning("Claude declined the blurb request; using the local copywriter")
            return self._fallback.write_blurb(brief)

        text = " ".join(
            block.text.strip() for block in response.content if block.type == "text"
        ).strip()
        return text[:MAX_BLURB_LENGTH] if text else self._fallback.write_blurb(brief)
