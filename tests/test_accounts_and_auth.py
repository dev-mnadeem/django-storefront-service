import pytest
from django.urls import reverse

from brand.services import accounts
from brand.services.accounts import RegistrationError, authenticate, register


def test_registration_stores_a_hash_not_the_password(customer):
    assert customer.password != "correct-horse-battery"
    assert customer.password.startswith("pbkdf2_")


def test_a_duplicate_email_is_refused_by_the_unique_index(customer):
    with pytest.raises(RegistrationError):
        register(
            first_name="Other",
            last_name="Person",
            phone="+923009999999",
            email=customer.email,
            password="another-password",
        )


def test_authenticate_accepts_the_right_password(customer):
    assert authenticate(email=customer.email, password="correct-horse-battery") == customer


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("dana@example.com", "wrong"),
        ("nobody@example.com", "correct-horse-battery"),
        ("dana@example.com", ""),
    ],
)
def test_authenticate_rejects_bad_credentials(customer, email, password):
    assert authenticate(email=email, password=password) is None


def test_email_match_is_case_insensitive(customer):
    assert authenticate(email="DANA@EXAMPLE.COM", password="correct-horse-battery")


@pytest.mark.django_db
def test_sign_in_cycles_the_session_key(rf, customer):
    from django.contrib.sessions.backends.db import SessionStore

    request = rf.get("/")
    request.session = SessionStore()
    request.session.create()
    planted_key = request.session.session_key

    accounts.sign_in(request, customer)

    assert request.session.session_key != planted_key
    assert accounts.current_customer_id(request) == customer.id


@pytest.mark.django_db
def test_sign_in_preserves_the_cart_across_the_key_rotation(rf, customer):
    from django.contrib.sessions.backends.db import SessionStore

    request = rf.get("/")
    request.session = SessionStore()
    request.session["cart"] = {"7": 2}
    accounts.sign_in(request, customer)
    assert request.session["cart"] == {"7": 2}


def test_anonymous_visitors_are_sent_to_login_with_a_next_parameter(client, db):
    response = client.get(reverse("orders"))
    assert response.status_code == 302
    assert response.headers["Location"] == "/login/?next=/orders/"


def test_signed_in_shoppers_reach_their_orders(signed_in_client):
    assert signed_in_client.get(reverse("orders")).status_code == 200


def test_logout_clears_the_session(signed_in_client):
    signed_in_client.get(reverse("logout"))
    assert "customer" not in signed_in_client.session
