import pytest
from django.urls import reverse

from brand.models.category import Category
from brand.models.product import Product


@pytest.fixture
def catalogue(db):
    shoes = Category.objects.create(name="Footwear")
    bags = Category.objects.create(name="Bags")
    for index in range(7):
        Product.objects.create(
            name=f"Runner {index}", price=1000 + index, category=shoes, stock=4
        )
    Product.objects.create(name="Rolltop Daypack", price=6900, category=bags, stock=0)
    return {"shoes": shoes, "bags": bags}


def test_the_catalogue_lists_every_product(client, catalogue):
    response = client.get(reverse("index"))
    assert response.status_code == 200
    assert response.context["page"].paginator.count == 8


def test_paging_splits_the_catalogue(client, catalogue, settings):
    settings.STOREFRONT_PAGE_SIZE = 3
    first = client.get(reverse("index"))
    assert len(first.context["products"]) == 3
    assert first.context["page"].paginator.num_pages == 3

    last = client.get(reverse("index"), {"page": 3})
    assert len(last.context["products"]) == 2


def test_an_out_of_range_page_falls_back_to_the_last_page(client, catalogue, settings):
    settings.STOREFRONT_PAGE_SIZE = 3
    response = client.get(reverse("index"), {"page": 999})
    assert response.context["page"].number == 3


def test_filtering_by_category(client, catalogue):
    response = client.get(reverse("index"), {"category": catalogue["bags"].id})
    assert [p.name for p in response.context["products"]] == ["Rolltop Daypack"]


def test_a_nonsense_category_returns_nothing_rather_than_erroring(client, catalogue):
    response = client.get(reverse("index"), {"category": "wat"})
    assert response.status_code == 200
    assert list(response.context["products"]) == []


def test_searching_by_name_is_case_insensitive(client, catalogue):
    response = client.get(reverse("index"), {"q": "rolltop"})
    assert [p.name for p in response.context["products"]] == ["Rolltop Daypack"]


def test_an_unmatched_search_renders_the_empty_state(client, catalogue):
    response = client.get(reverse("index"), {"q": "zzzz"})
    assert b"Nothing matches that" in response.content


def test_an_out_of_stock_product_cannot_be_added(client, catalogue):
    response = client.get(reverse("index"), {"category": catalogue["bags"].id})
    assert b"Out of stock" in response.content


def test_sidebar_counts_do_not_scale_with_the_number_of_categories(
    count_queries, client, catalogue
):
    """Category product counts come from one aggregate, not one query each."""
    baseline = count_queries("brand_category", lambda: client.get(reverse("index")))
    for name in ("Outerwear", "Accessories", "Kitchen", "Travel"):
        Category.objects.create(name=name)
    assert count_queries("brand_category", lambda: client.get(reverse("index"))) == baseline
    # One aggregate for the sidebar, plus the select_related join on the grid.
    assert baseline == 2


def test_adding_to_the_cart_redirects_back_to_the_product(client, catalogue):
    product = catalogue["shoes"].products.first()
    response = client.post(
        reverse("index"),
        {"product_id": product.id, "action": "add", "return_to": f"/#product-{product.id}"},
    )
    assert response.status_code == 302
    assert response.headers["Location"] == f"/#product-{product.id}"
    assert client.session["cart"] == {str(product.id): 1}


def test_a_malformed_cart_post_changes_nothing(client, catalogue):
    response = client.post(reverse("index"), {"product_id": "boom", "action": "add"})
    assert response.status_code == 302
    assert client.session.get("cart", {}) == {}
