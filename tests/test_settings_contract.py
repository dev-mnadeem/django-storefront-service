"""Settings must come from the environment, and refuse unsafe defaults."""

import importlib
import sys

import pytest
from django.core.exceptions import ImproperlyConfigured


def _reload_settings(monkeypatch, **env):
    for key in (
        "DJANGO_DEBUG",
        "DJANGO_SECRET_KEY",
        "DJANGO_ALLOWED_HOSTS",
        "STOREFRONT_PAGE_SIZE",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr("Eshop.settings._load_dotenv", lambda: None, raising=False)
    sys.modules.pop("Eshop.settings", None)
    return importlib.import_module("Eshop.settings")


def test_no_secret_key_is_hardcoded_for_production(monkeypatch):
    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        _reload_settings(monkeypatch, DJANGO_DEBUG="false")


def test_the_secret_key_is_read_from_the_environment(monkeypatch):
    module = _reload_settings(
        monkeypatch, DJANGO_DEBUG="false", DJANGO_SECRET_KEY="s3cr3t-from-env"
    )
    assert module.SECRET_KEY == "s3cr3t-from-env"
    assert module.DEBUG is False


def test_allowed_hosts_is_parsed_from_a_comma_list(monkeypatch):
    module = _reload_settings(
        monkeypatch,
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY="k",
        DJANGO_ALLOWED_HOSTS="shop.example.com, www.example.com",
    )
    assert module.ALLOWED_HOSTS == ["shop.example.com", "www.example.com"]


def test_debug_mode_supplies_a_throwaway_key_and_local_hosts(monkeypatch):
    module = _reload_settings(monkeypatch, DJANGO_DEBUG="true")
    assert module.DEBUG is True
    assert module.ALLOWED_HOSTS == ["localhost", "127.0.0.1"]


def test_page_size_is_configurable(monkeypatch):
    module = _reload_settings(monkeypatch, DJANGO_DEBUG="true", STOREFRONT_PAGE_SIZE="4")
    assert module.STOREFRONT_PAGE_SIZE == 4
