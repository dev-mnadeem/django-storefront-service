from django.db import models


class Category(models.Model):
    """A top-level grouping shown in the storefront sidebar."""

    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        return self.name
