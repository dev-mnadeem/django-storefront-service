from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from brand.auth import safe_redirect_target
from brand.forms import CartUpdateForm
from brand.services.cart import Cart, CartError
from brand.services.catalog import categories_with_counts, paginate, search_products


class Index(View):
    """The storefront: category filter, name search, paged product grid."""

    template_name = "index.html"

    def get(self, request):
        cart = Cart(request.session)
        category_id = request.GET.get("category") or ""
        query = (request.GET.get("q") or "").strip()
        page = paginate(
            search_products(category_id=category_id, query=query),
            request.GET.get("page"),
        )
        return render(
            request,
            self.template_name,
            {
                "page": page,
                "products": page.object_list,
                "categories": categories_with_counts(),
                "selected_category": str(category_id),
                "query": query,
                "cart_quantities": cart.raw,
            },
        )

    def post(self, request):
        """Apply one cart change, then redirect so a refresh cannot re-apply it."""
        form = CartUpdateForm(request.POST)
        if form.is_valid():
            cart = Cart(request.session)
            product_id = form.cleaned_data["product_id"]
            action = form.cleaned_data["action"]
            if action == "add":
                try:
                    cart.add_available(product_id)
                except CartError as exc:
                    messages.error(request, str(exc))
            elif action == "remove":
                cart.remove_one(product_id)
            else:
                cart.discard(product_id)
        # `return_to` comes from a hidden field, so it is as untrusted as `?next=`.
        return redirect(
            safe_redirect_target(request, request.POST.get("return_to"), reverse("index"))
        )
