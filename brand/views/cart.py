from django.shortcuts import render
from django.views import View

from brand.forms import CheckoutForm
from brand.services.cart import Cart


class CartView(View):
    """The cart page. Totals come from the service, not from the template."""

    template_name = "cart.html"

    def get(self, request):
        contents = Cart(request.session).contents()
        return render(
            request,
            self.template_name,
            {"cart": contents, "checkout_form": CheckoutForm()},
        )
