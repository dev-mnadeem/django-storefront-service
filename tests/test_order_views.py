import pytest
from django.urls import reverse

from brand.models.order import Order, OrderItem, OrderStatus


@pytest.fixture
def order(customer, product, second_product):
    order = Order.objects.create(
        customer=customer,
        address="12 Jinnah Road",
        phone=customer.phone,
        status=OrderStatus.SHIPPED,
    )
    OrderItem.objects.create(order=order, product=product, quantity=2, unit_price=product.price)
    OrderItem.objects.create(
        order=order, product=second_product, quantity=1, unit_price=second_product.price
    )
    order.recalculate_total()
    order.save(update_fields=["total_amount"])
    return order


def test_the_order_page_shows_lines_and_the_frozen_total(signed_in_client, order):
    response = signed_in_client.get(reverse("orders"))
    assert response.status_code == 200
    assert b"Trail Runner GT" in response.content
    assert order.total_amount == 8400 * 2 + 3200


def test_an_order_belonging_to_someone_else_is_not_listed(signed_in_client, order, db):
    from brand.services.accounts import register

    other = register(
        first_name="Sam",
        last_name="Rivera",
        phone="+923001111111",
        email="sam@example.com",
        password="another-good-password",
    )
    hidden = Order.objects.create(customer=other, address="elsewhere", phone="0")
    response = signed_in_client.get(reverse("orders"))
    assert hidden not in list(response.context["orders"])


def test_listing_orders_does_not_scale_queries_with_line_count(
    count_queries, signed_in_client, order, customer, category
):
    """Order lines and their products are prefetched, not fetched per row."""
    from brand.models.product import Product

    fetch = lambda: signed_in_client.get(reverse("orders"))  # noqa: E731
    baseline = count_queries("brand_product", fetch)

    extra = Order.objects.create(customer=customer, address="elsewhere", phone="0")
    for index in range(6):
        OrderItem.objects.create(
            order=extra,
            product=Product.objects.create(
                name=f"Filler {index}", price=100, category=category, stock=1
            ),
            quantity=1,
            unit_price=100,
        )

    assert count_queries("brand_product", fetch) == baseline
    assert baseline == 1


def test_checkout_is_closed_to_anonymous_visitors(client, product):
    response = client.post(
        reverse("checkout"), {"address": "12 Jinnah Road", "phone": "+923001234567"}
    )
    assert response.status_code == 302
    assert response.headers["Location"].startswith(reverse("login"))
    assert Order.objects.count() == 0


def test_a_successful_checkout_lands_on_the_order_page(signed_in_client, product):
    signed_in_client.post(reverse("index"), {"product_id": product.id, "action": "add"})
    response = signed_in_client.post(
        reverse("checkout"), {"address": "12 Jinnah Road", "phone": "+923001234567"}
    )
    assert response.status_code == 302
    assert response.headers["Location"] == reverse("orders")
    assert Order.objects.count() == 1


def test_checkout_without_an_address_re_renders_the_cart(signed_in_client, product):
    signed_in_client.post(reverse("index"), {"product_id": product.id, "action": "add"})
    response = signed_in_client.post(reverse("checkout"), {"phone": "+923001234567"})
    assert response.status_code == 400
    assert Order.objects.count() == 0


def test_checking_out_an_empty_cart_reports_an_error(signed_in_client):
    response = signed_in_client.post(
        reverse("checkout"),
        {"address": "12 Jinnah Road", "phone": "+923001234567"},
        follow=True,
    )
    assert b"Your cart is empty." in response.content


def test_the_cart_page_renders_for_anonymous_visitors(client, product):
    """The old cart view called .keys() on a missing session value and 500ed."""
    assert client.get(reverse("cart")).status_code == 200
