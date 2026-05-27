from django.core.validators import MinValueValidator
from django.db import models

from .category import Category


class ProductQuerySet(models.QuerySet):
    def in_stock(self) -> "ProductQuerySet":
        return self.filter(stock__gt=0)

    def with_category(self) -> "ProductQuerySet":
        """Join the category in the same query so templates do not trigger N+1."""
        return self.select_related("category")


class Product(models.Model):
    """A sellable item.

    `price` is a whole number of the storefront currency (see
    ``settings.STOREFRONT_CURRENCY_PREFIX``); there are no minor units, so an
    integer column is exact and avoids float rounding entirely.
    """

    name = models.CharField(max_length=50, db_index=True)
    price = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    desc = models.CharField(max_length=200, blank=True, default="")
    image = models.ImageField(upload_to="uploads/products/", blank=True)
    stock = models.PositiveIntegerField(default=0)

    objects = ProductQuerySet.as_manager()

    class Meta:
        ordering = ["name", "id"]
        indexes = [models.Index(fields=["category", "name"], name="product_cat_name_idx")]

    def __str__(self) -> str:
        return self.name

    @property
    def is_in_stock(self) -> bool:
        return self.stock > 0
