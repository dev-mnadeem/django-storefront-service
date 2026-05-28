from django.db import models


class Customer(models.Model):
    """A shopper account.

    `password` holds a Django password hash. It is written only through
    ``brand.services.accounts.register``, never from raw form input.
    """

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def full_name(self) -> str:
        return str(self)
