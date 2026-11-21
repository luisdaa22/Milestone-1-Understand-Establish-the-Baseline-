"""A new fulfillment option only needs a catalog entry (Milestone 2 design check)."""
import pytest
from sqlalchemy import select

from store import fulfillment
from store.db import get_session
from store.fulfillment import FulfillmentOption
from store.models import Order
from store.routes import checkout

SAME_DAY = FulfillmentOption("same_day", "Same-day courier", 14_900, True)
LOCKER = FulfillmentOption("locker", "Pickup locker", 2_900, False)

CUSTOMER = {
    "customer_name": "Ada Lovelace",
    "customer_email": "ada@example.com",
    "shipping_address": "123 Analytical Engine Way",
    "payment_token": "tok_success",
}


@pytest.fixture()
def extra_options(monkeypatch):
    options = fulfillment.FULFILLMENT_OPTIONS + (SAME_DAY, LOCKER)
    monkeypatch.setattr(checkout, "FULFILLMENT_OPTIONS", options)
    monkeypatch.setitem(fulfillment._BY_CODE, SAME_DAY.code, SAME_DAY)
    monkeypatch.setitem(fulfillment._BY_CODE, LOCKER.code, LOCKER)


def test_new_option_is_offered_on_the_checkout_page(client, first_product_id, extra_options):
    client.post(f"/cart/add/{first_product_id}")
    page = client.get("/checkout").data
    assert b"Same-day courier" in page
    assert b'value="same_day"' in page


@pytest.mark.parametrize(("option", "address"), [(SAME_DAY, "123 Analytical Engine Way"), (LOCKER, "")])
def test_new_option_is_charged_and_persisted(client, app, first_product_id, extra_options, option, address):
    client.post(f"/cart/add/{first_product_id}")
    response = client.post("/checkout", data={**CUSTOMER, "fulfillment_option": option.code, "shipping_address": address},
                           follow_redirects=True)
    assert option.label.encode() in response.data
    with app.app_context():
        order = get_session().scalar(select(Order))
        assert order.fulfillment_code == option.code
        assert order.shipping_cents == option.price_cents
        assert order.total_cents == 10_000 + option.price_cents


def test_new_option_that_needs_an_address_is_validated(client, app, first_product_id, extra_options):
    client.post(f"/cart/add/{first_product_id}")
    response = client.post("/checkout", data={**CUSTOMER, "fulfillment_option": "same_day", "shipping_address": ""},
                           follow_redirects=True)
    assert b"Please complete all checkout fields" in response.data
    with app.app_context():
        assert get_session().scalar(select(Order)) is None
