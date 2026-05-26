"""Reading the catalogue: filtering, searching, paging."""

from __future__ import annotations

from django.conf import settings
from django.core.paginator import Page, Paginator
from django.db.models import Count, QuerySet

from brand.models.category import Category
from brand.models.product import Product


def categories_with_counts() -> QuerySet[Category]:
    """Sidebar categories plus their product counts in one query."""
    return Category.objects.annotate(product_count=Count("products")).order_by("name")


def search_products(
    *, category_id: str | int | None = None, query: str | None = None
) -> QuerySet[Product]:
    products = Product.objects.with_category()
    if category_id not in (None, ""):
        try:
            products = products.filter(category_id=int(category_id))
        except (TypeError, ValueError):
            return products.none()
    if query:
        products = products.filter(name__icontains=query.strip())
    return products


def paginate(products: QuerySet[Product], page_number) -> Page:
    """Page the catalogue so an unbounded table never reaches a template."""
    paginator = Paginator(products, settings.STOREFRONT_PAGE_SIZE)
    return paginator.get_page(page_number)
