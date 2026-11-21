"""Fulfillment options offered at checkout (Milestone 2).

Each option is plain data: a code saved on the Order, a label for the UI,
its price and whether it needs a shipping address. The options differ only
in these values, not in behaviour, so a small immutable catalog is enough.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FulfillmentOption:
    code: str
    label: str
    price_cents: int
    requires_address: bool


FULFILLMENT_OPTIONS: tuple[FulfillmentOption, ...] = (
    FulfillmentOption("standard", "Standard shipping", 9_900, True),
    FulfillmentOption("express", "Express shipping", 19_900, True),
    FulfillmentOption("pickup", "Store pickup", 0, False),
)

DEFAULT_OPTION = "standard"

_BY_CODE = {option.code: option for option in FULFILLMENT_OPTIONS}


def get_option(code: str | None) -> FulfillmentOption | None:
    """Return the option for ``code``, or ``None`` if it is not offered."""
    return _BY_CODE.get((code or "").strip())
