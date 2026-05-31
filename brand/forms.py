"""Request validation.

Django forms replace the hand-rolled `validatecustomer` chain, which returned
one string at a time and crashed on a missing email (`len(None)`).
"""

from django import forms

MIN_NAME_LENGTH = 2
MIN_PHONE_LENGTH = 7
MIN_PASSWORD_LENGTH = 8


class StorefrontForm(forms.Form):
    """Shared base: drop Django's trailing ":" so labels match the design."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)


class SignupForm(StorefrontForm):
    first_name = forms.CharField(label="First name", max_length=50, min_length=MIN_NAME_LENGTH)
    last_name = forms.CharField(label="Last name", max_length=50, min_length=MIN_NAME_LENGTH)
    email = forms.EmailField(label="Email", max_length=254)
    phone = forms.CharField(label="Phone", max_length=15, min_length=MIN_PHONE_LENGTH)
    password = forms.CharField(
        label="Password",
        min_length=MIN_PASSWORD_LENGTH,
        widget=forms.PasswordInput,
        help_text=f"At least {MIN_PASSWORD_LENGTH} characters.",
    )

    def clean_email(self) -> str:
        return self.cleaned_data["email"].strip().lower()

    def clean_phone(self) -> str:
        phone = self.cleaned_data["phone"].strip()
        if not phone.lstrip("+").replace(" ", "").replace("-", "").isdigit():
            raise forms.ValidationError("Enter digits only, optionally starting with +.")
        return phone


class LoginForm(StorefrontForm):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class CheckoutForm(StorefrontForm):
    address = forms.CharField(label="Delivery address", max_length=200)
    phone = forms.CharField(label="Phone", max_length=50)


class CartUpdateForm(StorefrontForm):
    """One +/- click on a product card."""

    ACTIONS = (("add", "add"), ("remove", "remove"), ("drop", "drop"))

    product_id = forms.IntegerField(min_value=1)
    action = forms.ChoiceField(choices=ACTIONS)
