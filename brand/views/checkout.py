from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from brand.forms import CheckoutForm
from brand.services.accounts import current_customer_id
from brand.services.cart import Cart
from brand.services.checkout import CheckoutError, place_order


class CheckOut(View):
    """POST-only. Delegates every rule to `brand.services.checkout`."""

    def post(self, request):
        form = CheckoutForm(request.POST)
        cart = Cart(request.session)
        if not form.is_valid():
            return render(
                request,
                "cart.html",
                {"cart": cart.contents(), "checkout_form": form},
                status=400,
            )
        try:
            order = place_order(
                customer_id=current_customer_id(request),
                cart=cart,
                address=form.cleaned_data["address"],
                phone=form.cleaned_data["phone"],
            )
        except CheckoutError as exc:
            messages.error(request, str(exc))
            return redirect("cart")
        messages.success(request, f"Order #{order.pk} placed. Thank you!")
        return redirect("orders")
