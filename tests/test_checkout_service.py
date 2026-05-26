import pytest
from django.contrib.sessions.backends.db import SessionStore

from brand.models.order import Order, OrderStatus
from brand.models.product import Product
from brand.services.cart import Cart
from brand.services.checkout import CheckoutError, place_order


@pytest.fixture
def cart(db) -> Cart:
    return Cart(SessionStore())


def _place(customer, cart, address="12 Jinnah Road", phone="+923001234567"):
    return place_order(customer_id=customer.id, cart=cart, address=address, phone=phone)


def test_placing_an_order_creates_lines_and_a_total(cart, customer, product):
    cart.add(product.id, delta=2)
    order = _place(customer, cart)
    assert order.status == OrderStatus.PENDING
    assert order.total_amount == product.price * 2
    assert order.items.count() == 1


def test_unit_price_is_read_from_the_database_not_the_session(cart, customer, product):
    """Regression: the price on an order line must come from the product row."""
    cart.add(product.id)
    cart.raw["price"] = 1  # an attacker-controlled key in the session cart
    cart.raw[str(product.id)] = 1
    order = _place(customer, cart)
    assert order.items.get().unit_price == product.price


def test_a_later_price_change_does_not_rewrite_order_history(cart, customer, product):
    cart.add(product.id)
    order = _place(customer, cart)
    Product.objects.filter(id=product.id).update(price=99999)
    order.refresh_from_db()
    assert order.items.get().unit_price == 8400
    assert order.total_amount == 8400


def test_checkout_decrements_stock(cart, customer, product):
    cart.add(product.id, delta=3)
    _place(customer, cart)
    product.refresh_from_db()
    assert product.stock == 2


def test_ordering_more_than_stock_is_refused_and_rolls_back(cart, customer, product):
    cart.add(product.id, delta=99)
    with pytest.raises(CheckoutError, match="left in stock"):
        _place(customer, cart)
    product.refresh_from_db()
    assert product.stock == 5
    assert Order.objects.count() == 0


def test_a_partially_unavailable_cart_leaves_no_order_behind(
    cart, customer, product, second_product
):
    cart.add(product.id, delta=1)
    cart.add(second_product.id, delta=999)
    with pytest.raises(CheckoutError):
        _place(customer, cart)
    assert Order.objects.count() == 0
    product.refresh_from_db()
    assert product.stock == 5


def test_an_empty_cart_cannot_be_checked_out(cart, customer):
    with pytest.raises(CheckoutError, match="empty"):
        _place(customer, cart)


def test_a_blank_address_is_refused(cart, customer, product):
    cart.add(product.id)
    with pytest.raises(CheckoutError, match="address"):
        _place(customer, cart, address="   ")


def test_the_cart_is_emptied_once_the_order_exists(cart, customer, product):
    cart.add(product.id)
    _place(customer, cart)
    assert cart.raw == {}
