"""Populate the storefront with a browsable demo catalogue.

Everything this creates is fake and idempotent: running it twice leaves the
same rows. Product images are drawn locally with Pillow so the command needs no
network and ships no third-party artwork.
"""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from brand.ai import ProductBrief, get_copywriter
from brand.models.category import Category
from brand.models.customer import Customer
from brand.models.order import Order, OrderItem, OrderStatus
from brand.models.product import Product
from brand.services.accounts import register

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo-password"

CATALOGUE: dict[str, list[tuple[str, int, int]]] = {
    "Footwear": [
        ("Trail Runner GT", 8400, 14),
        ("Canvas Low Top", 3200, 26),
        ("Leather Chelsea Boot", 12800, 6),
        ("Recovery Slide", 1900, 40),
    ],
    "Outerwear": [
        ("Packable Rain Shell", 9600, 11),
        ("Quilted Liner Jacket", 11500, 8),
        ("Merino Overshirt", 7300, 17),
    ],
    "Bags": [
        ("Rolltop Daypack", 6900, 21),
        ("Weekender Duffel", 10400, 9),
        ("Cordura Sling", 3400, 33),
    ],
    "Accessories": [
        ("Ribbed Wool Beanie", 1600, 52),
        ("Webbing Belt", 2100, 38),
        ("Leather Card Holder", 2800, 24),
        ("Steel Water Bottle", 2450, 30),
    ],
}

# Muted, high-contrast card art so the grid reads well in a screenshot.
PALETTE = [
    ((32, 44, 61), (86, 110, 140)),
    ((58, 38, 34), (150, 104, 86)),
    ((28, 52, 46), (92, 140, 118)),
    ((52, 34, 56), (132, 96, 140)),
    ((60, 52, 28), (156, 140, 84)),
]

IMAGE_SIZE = (900, 900)


def _draw_product_image(name: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    seed = int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "big")
    top, bottom = PALETTE[seed % len(PALETTE)]
    width, height = IMAGE_SIZE
    image = Image.new("RGB", IMAGE_SIZE, top)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / height
        draw.line(
            [(0, y), (width, y)],
            fill=tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)),
        )

    # A pair of off-centre circles keeps each card visually distinct.
    for offset, alpha in ((0, 26), (1, 16)):
        radius = 190 + ((seed >> (4 * (offset + 1))) % 140)
        cx = 180 + ((seed >> (3 * (offset + 1))) % 540)
        cy = 200 + ((seed >> (5 * (offset + 1))) % 500)
        overlay = Image.new("RGBA", IMAGE_SIZE, (255, 255, 255, 0))
        ImageDraw.Draw(overlay).ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=(255, 255, 255, alpha),
        )
        image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(image)
    initials = "".join(word[0] for word in name.split()[:3]).upper()
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Futura.ttc", 220)
    except OSError:
        font = ImageFont.load_default(size=180)
    box = draw.textbbox((0, 0), initials, font=font)
    draw.text(
        ((width - box[2] + box[0]) / 2, (height - box[3] + box[1]) / 2),
        initials,
        font=font,
        fill=(255, 255, 255),
    )

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue()


class Command(BaseCommand):
    help = "Create demo categories, products, a shopper, and a sample order."

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-images",
            action="store_true",
            help="Skip generating product artwork (faster, but cards render blank).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        copywriter = get_copywriter()
        Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

        products: list[Product] = []
        for category_name, rows in CATALOGUE.items():
            category, _ = Category.objects.get_or_create(name=category_name)
            for product_name, price, stock in rows:
                product, created = Product.objects.get_or_create(
                    name=product_name,
                    defaults={
                        "category": category,
                        "price": price,
                        "stock": stock,
                    },
                )
                if not created:
                    product.category = category
                    product.price = price
                    product.stock = stock
                if not product.desc:
                    product.desc = copywriter.write_blurb(
                        ProductBrief(name=product_name, category=category_name, price=price)
                    )
                if not options["no_images"] and not product.image:
                    product.image.save(
                        f"{product_name.lower().replace(' ', '-')}.jpg",
                        ContentFile(_draw_product_image(product_name)),
                        save=False,
                    )
                product.save()
                products.append(product)

        customer = Customer.objects.filter(email=DEMO_EMAIL).first()
        if customer is None:
            customer = register(
                first_name="Dana",
                last_name="Okafor",
                phone="+923001234567",
                email=DEMO_EMAIL,
                password=DEMO_PASSWORD,
            )

        if not Order.objects.filter(customer=customer).exists():
            self._create_demo_order(
                customer, products[:2], OrderStatus.SHIPPED, "12 Jinnah Road, Lahore"
            )
            self._create_demo_order(
                customer, products[4:6], OrderStatus.PENDING, "12 Jinnah Road, Lahore"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Category.objects.count()} categories, "
                f"{Product.objects.count()} products, "
                f"{Order.objects.count()} orders. "
                f"Sign in as {DEMO_EMAIL} / {DEMO_PASSWORD}"
            )
        )

    def _create_demo_order(self, customer, products, status, address) -> None:
        order = Order.objects.create(
            customer=customer,
            address=address,
            phone=customer.phone,
            status=status,
            total_amount=0,
        )
        for index, product in enumerate(products, start=1):
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=index,
                unit_price=product.price,
            )
        order.recalculate_total()
        order.save(update_fields=["total_amount"])
