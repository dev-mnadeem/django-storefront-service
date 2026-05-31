from django.contrib import admin, messages

from brand.ai import ProductBrief, get_copywriter
from brand.models.category import Category
from brand.models.customer import Customer
from brand.models.order import Order, OrderItem
from brand.models.product import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "category", "stock"]
    list_filter = ["category"]
    search_fields = ["name"]
    list_select_related = ["category"]
    actions = ["generate_descriptions"]

    @admin.action(description="Generate a description for products missing one")
    def generate_descriptions(self, request, queryset):
        copywriter = get_copywriter()
        written = 0
        for product in queryset.select_related("category"):
            if product.desc.strip():
                continue
            product.desc = copywriter.write_blurb(
                ProductBrief(
                    name=product.name,
                    category=product.category.name,
                    price=product.price,
                )
            )
            product.save(update_fields=["desc"])
            written += 1
        self.message_user(
            request,
            f"Wrote {written} description(s) with the '{copywriter.name}' copywriter.",
            messages.SUCCESS,
        )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "email"]
    search_fields = ["first_name", "last_name", "email"]
    readonly_fields = ["password"]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["unit_price"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "customer", "placed_at", "status", "total_amount"]
    list_filter = ["status"]
    list_select_related = ["customer"]
    date_hierarchy = "placed_at"
    inlines = [OrderItemInline]
