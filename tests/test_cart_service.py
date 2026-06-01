import pytest
from django.contrib.sessions.backends.db import SessionStore

from brand.services.cart import Cart


@pytest.fixture
def cart(db) -> Cart:
    return Cart(SessionStore())


def test_new_session_starts_with_an_empty_cart(cart):
    assert cart.raw == {}
    assert cart.item_count == 0


def test_add_accumulates_then_remove_one_decrements(cart, product):
    cart.add(product.id)
    cart.add(product.id)
    assert cart.quantity_of(product.id) == 2
    cart.remove_one(product.id)
    assert cart.quantity_of(product.id) == 1


def test_removing_the_last_unit_drops_the_line(cart, product):
    cart.add(product.id)
    cart.remove_one(product.id)
    assert str(product.id) not in cart.raw


def test_quantity_is_clamped_to_the_configured_ceiling(cart, product, settings):
    settings.CART_MAX_QUANTITY_PER_LINE = 3
    for _ in range(10):
        cart.add(product.id)
    assert cart.quantity_of(product.id) == 3


def test_contents_totals_each_line_and_the_whole_cart(cart, product, second_product):
    cart.add(product.id, delta=2)
    cart.add(second_product.id)
    contents = cart.contents()
    assert contents.item_count == 3
    assert contents.total == product.price * 2 + second_product.price
    assert [line.line_total for line in contents.lines] == [
        second_product.price,
        product.price * 2,
    ]


def test_contents_issues_one_query_regardless_of_line_count(
    django_assert_num_queries, cart, product, second_product
):
    cart.add(product.id)
    cart.add(second_product.id)
    with django_assert_num_queries(1):
        cart.contents()


def test_ids_for_deleted_products_are_pruned_from_the_session(cart, product):
    cart.add(product.id)
    product_id = product.id
    product.delete()
    assert cart.contents().is_empty
    assert str(product_id) not in cart.raw


def test_a_corrupt_session_value_is_replaced_rather_than_raising(db):
    session = SessionStore()
    session["cart"] = "not-a-dict"
    assert Cart(session).raw == {}
