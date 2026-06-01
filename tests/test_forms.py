import pytest

from brand.forms import CartUpdateForm, SignupForm

VALID = {
    "first_name": "Dana",
    "last_name": "Okafor",
    "email": "Dana@Example.COM",
    "phone": "+923001234567",
    "password": "correct-horse-battery",
}


def test_a_complete_signup_validates_and_normalises_the_email():
    form = SignupForm(VALID)
    assert form.is_valid()
    assert form.cleaned_data["email"] == "dana@example.com"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("first_name", ""),
        ("first_name", "D"),
        ("last_name", ""),
        ("email", "not-an-email"),
        ("email", ""),
        ("phone", "12"),
        ("phone", "not-a-number"),
        ("password", "short"),
        ("password", ""),
    ],
)
def test_signup_rejects_each_bad_field(field, value):
    form = SignupForm({**VALID, field: value})
    assert not form.is_valid()
    assert field in form.errors


def test_a_missing_email_reports_an_error_instead_of_crashing():
    """The old hand-rolled validator ran len(None) on a missing email."""
    form = SignupForm({k: v for k, v in VALID.items() if k != "email"})
    assert not form.is_valid()
    assert form.errors["email"] == ["This field is required."]


@pytest.mark.parametrize(
    "payload",
    [
        {"product_id": "abc", "action": "add"},
        {"product_id": "-1", "action": "add"},
        {"product_id": "1", "action": "delete-everything"},
        {"action": "add"},
    ],
)
def test_cart_updates_reject_malformed_input(payload):
    assert not CartUpdateForm(payload).is_valid()
