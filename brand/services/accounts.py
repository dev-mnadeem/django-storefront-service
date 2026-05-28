"""Shopper registration, sign-in, and the session contract.

A signed-in shopper is represented by ``request.session["customer"]`` holding a
`Customer` primary key. `brand.auth` is the only other module that reads it.
"""

from __future__ import annotations

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError

from brand.models.customer import Customer

SESSION_KEY = "customer"


class RegistrationError(Exception):
    """The account could not be created."""


def register(
    *, first_name: str, last_name: str, phone: str, email: str, password: str
) -> Customer:
    """Create a shopper. The unique index on `email` is the real guard.

    A pre-flight "does this email exist" query would still race two concurrent
    signups, so the IntegrityError is what we catch.
    """
    try:
        return Customer.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            email=email,
            password=make_password(password),
        )
    except IntegrityError as exc:
        raise RegistrationError("An account with that email already exists.") from exc


def authenticate(*, email: str, password: str) -> Customer | None:
    """Return the customer when the credentials match, else None.

    The dummy hash on the miss path keeps the response time of "unknown email"
    close to "wrong password", so the endpoint does not enumerate accounts.
    """
    customer = Customer.objects.filter(email__iexact=(email or "").strip()).first()
    if customer is None:
        make_password(password or "")
        return None
    if not check_password(password or "", customer.password):
        return None
    return customer


def sign_in(request, customer: Customer) -> None:
    """Attach the customer to the session with a fresh session key.

    Cycling the key is what stops session fixation: a key an attacker planted
    before sign-in is not the key that ends up authenticated.
    """
    cart = request.session.get("cart", {})
    request.session.cycle_key()
    request.session[SESSION_KEY] = customer.id
    request.session["cart"] = cart


def sign_out(request) -> None:
    request.session.flush()


def current_customer_id(request) -> int | None:
    value = request.session.get(SESSION_KEY)
    return value if isinstance(value, int) else None
