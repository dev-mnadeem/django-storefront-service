from brand.ai import ProductBrief, get_copywriter
from brand.ai.base import MAX_BLURB_LENGTH
from brand.ai.local import LocalCopywriter

BRIEF = ProductBrief(name="Trail Runner GT", category="Footwear", price=8400)


def test_the_default_backend_needs_no_api_key(settings):
    settings.COPYWRITER_BACKEND = "local"
    settings.ANTHROPIC_API_KEY = ""
    assert get_copywriter().name == "local"


def test_an_unknown_backend_falls_back_to_local(settings):
    settings.COPYWRITER_BACKEND = "hal9000"
    assert isinstance(get_copywriter(), LocalCopywriter)


def test_the_anthropic_backend_is_selected_by_configuration(settings):
    settings.COPYWRITER_BACKEND = "anthropic"
    assert get_copywriter().name == "anthropic"


def test_the_local_copywriter_is_deterministic():
    first = LocalCopywriter().write_blurb(BRIEF)
    second = LocalCopywriter().write_blurb(BRIEF)
    assert first == second


def test_different_products_get_different_copy():
    other = ProductBrief(name="Rolltop Daypack", category="Bags", price=6900)
    assert LocalCopywriter().write_blurb(BRIEF) != LocalCopywriter().write_blurb(other)


def test_the_blurb_names_the_product_and_its_price():
    blurb = LocalCopywriter().write_blurb(BRIEF)
    assert "Trail Runner GT" in blurb
    assert "Rs. 8,400" in blurb


def test_the_blurb_fits_the_desc_column():
    long_brief = ProductBrief(name="X" * 180, category="Footwear", price=1)
    assert len(LocalCopywriter().write_blurb(long_brief)) <= MAX_BLURB_LENGTH


def test_the_anthropic_backend_degrades_to_local_without_a_key(settings):
    from brand.ai.anthropic_provider import AnthropicCopywriter

    settings.ANTHROPIC_API_KEY = ""
    blurb = AnthropicCopywriter().write_blurb(BRIEF)
    assert blurb == LocalCopywriter().write_blurb(BRIEF)
