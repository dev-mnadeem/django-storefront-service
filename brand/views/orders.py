from django.shortcuts import render
from django.views import View

from brand.models.order import Order
from brand.services.accounts import current_customer_id


class OrderView(View):
    """Order history for the signed-in shopper."""

    template_name = "order.html"

    def get(self, request):
        orders = Order.objects.for_customer(current_customer_id(request)).with_lines().all()
        return render(request, self.template_name, {"orders": orders})
