import pytest
from django.core.management import call_command

from brand.management.commands.seed_demo import CATALOGUE, DEMO_EMAIL, DEMO_PASSWORD
from brand.models import Category, Customer, Order, Product
from brand.services.accounts import authenticate


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)
    return tmp_path


def seed():
    call_command("seed_demo", "--no-images", verbosity=0)


@pytest.mark.django_db
def test_seeding_builds_the_demo_catalogue_and_shopper(media):
    seed()
    assert Category.objects.count() == len(CATALOGUE)
    assert Product.objects.count() == sum(len(rows) for rows in CATALOGUE.values())
    assert authenticate(email=DEMO_EMAIL, password=DEMO_PASSWORD) is not None
    assert Order.objects.count() == 2
    assert all(order.total_amount > 0 for order in Order.objects.all())


@pytest.mark.django_db
def test_seeding_twice_creates_nothing_new(media):
    seed()
    counts = (Product.objects.count(), Customer.objects.count(), Order.objects.count())
    seed()
    assert (Product.objects.count(), Customer.objects.count(), Order.objects.count()) == counts


@pytest.mark.django_db
def test_reseeding_keeps_stock_and_price_changes(media):
    """Compose seeds on every start; a restart must not undo sales or repricing."""
    seed()
    boot = Product.objects.get(name="Leather Chelsea Boot")
    boot.stock = 1
    boot.price = 9999
    boot.save()

    seed()

    boot.refresh_from_db()
    assert (boot.stock, boot.price) == (1, 9999)
