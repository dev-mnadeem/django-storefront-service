from django.urls import path

from brand.auth import customer_required
from brand.views.cart import CartView
from brand.views.checkout import CheckOut
from brand.views.health import healthz
from brand.views.home import Index
from brand.views.login import Login, logout
from brand.views.orders import OrderView
from brand.views.signup import Signup

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("healthz/", healthz, name="healthz"),
    path("signup/", Signup.as_view(), name="signup"),
    path("login/", Login.as_view(), name="login"),
    path("logout/", logout, name="logout"),
    path("cart/", CartView.as_view(), name="cart"),
    path("checkout/", customer_required(CheckOut.as_view()), name="checkout"),
    path("orders/", customer_required(OrderView.as_view()), name="orders"),
]
