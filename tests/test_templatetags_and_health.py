import pytest
from django.urls import reverse

from brand.templatetags.cart import cart_quantity, currency


def test_currency_uses_the_configured_prefix(settings):
    settings.STOREFRONT_CURRENCY_PREFIX = "Rs. "
    assert currency(8400) == "Rs. 8,400"


def test_currency_survives_a_missing_value():
    assert currency(None) == "Rs. 0"


class _FakeProduct:
    id = 7


@pytest.mark.parametrize(
    ("quantities", "expected"),
    [({}, 0), (None, 0), ({"7": 3}, 3), ({"8": 3}, 0)],
)
def test_cart_quantity_reads_the_session_dict(quantities, expected):
    assert cart_quantity(_FakeProduct(), quantities) == expected


def test_healthz_reports_ok_with_a_working_database(client, db):
    response = client.get(reverse("healthz"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_an_unknown_url_renders_the_custom_404(client, db, settings):
    settings.DEBUG = False
    settings.ALLOWED_HOSTS = ["testserver"]
    response = client.get("/no-such-page/")
    assert response.status_code == 404
    assert b"that page does not exist" in response.content
