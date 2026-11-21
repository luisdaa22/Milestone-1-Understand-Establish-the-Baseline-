"""Unit tests for the fulfillment option catalog (Milestone 2)."""
import dataclasses

import pytest

from store.fulfillment import DEFAULT_OPTION, FULFILLMENT_OPTIONS, get_option


@pytest.mark.parametrize(
    ("code", "price_cents", "requires_address"),
    [
        ("standard", 9_900, True),
        ("express", 19_900, True),
        ("pickup", 0, False),
    ],
)
def test_each_option_has_its_price_and_address_rule(code, price_cents, requires_address):
    option = get_option(code)
    assert option is not None
    assert option.code == code
    assert option.price_cents == price_cents
    assert option.requires_address is requires_address
    assert option.label


@pytest.mark.parametrize("code", ["overnight", "STANDARD", "", None])
def test_unknown_code_returns_none(code):
    assert get_option(code) is None


def test_code_with_surrounding_spaces_is_accepted():
    assert get_option("  pickup ").code == "pickup"


def test_default_option_is_standard_and_offered():
    assert DEFAULT_OPTION == "standard"
    assert get_option(DEFAULT_OPTION) is not None


def test_catalog_has_three_unique_codes_in_display_order():
    assert [option.code for option in FULFILLMENT_OPTIONS] == ["standard", "express", "pickup"]


def test_options_are_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        get_option("standard").price_cents = 0
