from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from brand.forms import SignupForm
from brand.services import accounts


class Signup(View):
    template_name = "signup.html"

    def get(self, request):
        return render(request, self.template_name, {"form": SignupForm()})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            try:
                accounts.register(**form.cleaned_data)
            except accounts.RegistrationError as exc:
                form.add_error("email", str(exc))
            else:
                messages.success(request, "Account created. Please sign in.")
                return redirect("login")
        return render(request, self.template_name, {"form": form}, status=400)
