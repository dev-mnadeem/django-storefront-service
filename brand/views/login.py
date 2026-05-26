from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from brand.auth import REDIRECT_FIELD_NAME, safe_redirect_target
from brand.forms import LoginForm
from brand.services import accounts


class Login(View):
    """Sign-in.

    The post-login destination is read per request and validated against this
    host. It is deliberately not stored on the class: a class attribute would
    be shared by every visitor of every session.
    """

    template_name = "login.html"

    def get(self, request):
        return render(
            request,
            self.template_name,
            {"form": LoginForm(), "next": request.GET.get(REDIRECT_FIELD_NAME, "")},
        )

    def post(self, request):
        form = LoginForm(request.POST)
        requested_next = request.POST.get(REDIRECT_FIELD_NAME, "")
        destination = safe_redirect_target(request, requested_next, reverse("index"))
        if form.is_valid():
            customer = accounts.authenticate(
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if customer is not None:
                accounts.sign_in(request, customer)
                return redirect(destination)
            form.add_error(None, "Email or password is incorrect.")
        return render(
            request,
            self.template_name,
            {"form": form, "next": requested_next},
            status=400,
        )


def logout(request):
    accounts.sign_out(request)
    return redirect("login")
