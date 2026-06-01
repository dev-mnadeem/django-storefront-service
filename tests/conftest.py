import pytest

from brand.models.category import Category
from brand.models.customer import Customer
from brand.models.product import Product
from brand.services.accounts import register


@pytest.fixture
def category(db) -> Category:
    return Category.objects.create(name="Footwear")


@pytest.fixture
def product(category) -> Product:
    return Product.objects.create(
        name="Trail Runner GT", price=8400, category=category, stock=5
    )


@pytest.fixture
def second_product(category) -> Product:
    return Product.objects.create(
        name="Canvas Low Top", price=3200, category=category, stock=12
    )


@pytest.fixture
def customer(db) -> Customer:
    return register(
        first_name="Dana",
        last_name="Okafor",
        phone="+923001234567",
        email="dana@example.com",
        password="correct-horse-battery",
    )


@pytest.fixture
def signed_in_client(client, customer):
    session = client.session
    session["customer"] = customer.id
    session.save()
    return client


@pytest.fixture
def count_queries():
    """Count only the queries that touch a given table during a request.

    Session and savepoint statements are noise for an N+1 assertion, so they
    are filtered out and the interesting table is counted on its own.
    """
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    def _count(table: str, call):
        with CaptureQueriesContext(connection) as captured:
            call()
        return sum(1 for query in captured.captured_queries if table in query["sql"])

    return _count
