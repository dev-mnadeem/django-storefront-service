"""Access control for shopper-only pages."""

from __future__ import annotations

from functools import wraps

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from brand.services.accounts import current_customer_id

REDIRECT_FIELD_NAME = "next"


def safe_redirect_target(request, candidate: str | None, fallback: str) -> str:
    """Return `candidate` only if it points back at this site.

    Without this check ``/login/?next=https://example.com`` would make the
    storefront bounce a freshly authenticated shopper to any attacker URL.
    """
    if candidate and url_has_allowed_host_and_scheme(
        url=candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return fallback


def customer_required(view):
    """Send anonymous visitors to the sign-in page, remembering where they were.

    Replaces the old hand-rolled middleware, which hardcoded
    ``http://127.0.0.1:8000/login/`` and dropped the originally requested page.
    """

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if current_customer_id(request) is None:
            login_url = reverse("login")
            return redirect(f"{login_url}?{REDIRECT_FIELD_NAME}={request.get_full_path()}")
        return view(request, *args, **kwargs)

    return wrapper
