"""The post-login redirect target.

Two defects are pinned here: the target must not leave this host, and it must
not leak between requests (it used to live on a class attribute).
"""

import pytest
from django.urls import reverse

CREDENTIALS = {"email": "dana@example.com", "password": "correct-horse-battery"}


@pytest.mark.parametrize(
    "hostile",
    [
        "https://evil.example.com/harvest",
        "//evil.example.com/harvest",
        "http://127.0.0.1:9999/",
    ],
)
def test_an_off_site_next_is_ignored(client, customer, hostile):
    response = client.post(reverse("login"), {**CREDENTIALS, "next": hostile})
    assert response.status_code == 302
    assert response.headers["Location"] == reverse("index")


def test_a_relative_next_is_honoured(client, customer):
    response = client.post(reverse("login"), {**CREDENTIALS, "next": "/orders/"})
    assert response.headers["Location"] == "/orders/"


def test_one_visitors_next_does_not_follow_another_visitor(client, customer, django_user_model):
    from django.test import Client

    from brand.services.accounts import register

    other = register(
        first_name="Sam",
        last_name="Rivera",
        phone="+923001111111",
        email="sam@example.com",
        password="another-good-password",
    )
    # Visitor A asks to be returned to /orders/ but never completes sign-in.
    client.get(f"{reverse('login')}?next=/orders/")

    # Visitor B signs in from a different browser with no `next` at all.
    response = Client().post(
        reverse("login"), {"email": other.email, "password": "another-good-password"}
    )
    assert response.headers["Location"] == reverse("index")


def test_bad_credentials_re_render_the_form_with_an_error(client, customer):
    response = client.post(reverse("login"), {**CREDENTIALS, "password": "nope"})
    assert response.status_code == 400
    assert b"Email or password is incorrect." in response.content
