"""Checkout behaviour for the fulfillment options Change Request (Milestone 2)."""
import re

import pytest
from sqlalchemy import func, select

from store.db import get_session
from store.models import Order, Product

CUSTOMER = {
    "customer_name": "Ada Lovelace",
    "customer_email": "ada@example.com",
    "shipping_address": "123 Analytical Engine Way",
    "payment_token": "tok_success",
}


def _order_count(app):
    with app.app_context():
        return get_session().scalar(select(func.count()).select_from(Order))


def _only_order(app):
    with app.app_context():
        return get_session().scalar(select(Order))


def _checkout(client, product_id, **form):
    client.post(f"/cart/add/{product_id}")
    return client.post("/checkout", data={**CUSTOMER, **form}, follow_redirects=True)


@pytest.mark.parametrize(
    ("code", "shipping_cents"),
    [("standard", 9_900), ("express", 19_900), ("pickup", 0)],
)
def test_each_option_sets_shipping_total_and_is_persisted(client, app, first_product_id, code, shipping_cents):
    response = _checkout(client, first_product_id, fulfillment_option=code)
    assert b"Order #1" in response.data
    order = _only_order(app)
    assert order.fulfillment_code == code
    assert order.shipping_cents == shipping_cents
    assert order.total_cents == 10_000 + shipping_cents


def test_missing_option_defaults_to_standard(client, app, first_product_id):
    _checkout(client, first_product_id)  # form without fulfillment_option
    order = _only_order(app)
    assert order.fulfillment_code == "standard"
    assert order.shipping_cents == 9_900


def test_pickup_does_not_require_an_address(client, app, first_product_id):
    response = _checkout(client, first_product_id, fulfillment_option="pickup", shipping_address="")
    assert b"Order #1" in response.data
    assert _only_order(app).shipping_address == ""


def test_pickup_ignores_an_address_typed_by_mistake(client, app, first_product_id):
    _checkout(client, first_product_id, fulfillment_option="pickup")
    assert _only_order(app).shipping_address == ""


@pytest.mark.parametrize("code", ["standard", "express"])
def test_shipping_options_require_an_address(client, app, first_product_id, code):
    response = _checkout(client, first_product_id, fulfillment_option=code, shipping_address="  ")
    assert b"Please complete all checkout fields" in response.data
    assert _order_count(app) == 0


def test_invalid_option_is_rejected_without_charging_or_saving(client, app, first_product_id):
    response = _checkout(client, first_product_id, fulfillment_option="drone")
    assert b"Please choose a valid fulfillment option" in response.data
    assert _order_count(app) == 0
    with app.app_context():
        assert get_session().get(Product, first_product_id).stock_quantity == 5


@pytest.mark.parametrize("code", ["standard", "express", "pickup"])
def test_every_option_still_decrements_inventory(client, app, first_product_id, code):
    _checkout(client, first_product_id, fulfillment_option=code)
    with app.app_context():
        assert get_session().get(Product, first_product_id).stock_quantity == 4


def test_declined_payment_with_express_creates_no_order(client, app, first_product_id):
    response = _checkout(client, first_product_id, fulfillment_option="express", payment_token="tok_fail")
    assert b"Payment was declined" in response.data
    assert _order_count(app) == 0


def test_checkout_page_lists_all_options_with_standard_selected(client, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    page = client.get("/checkout").data
    for label in (b"Standard shipping", b"Express shipping", b"Store pickup"):
        assert label in page
    checked = re.findall(rb'value="(\w+)"[^>]*\bchecked\b', page)
    assert checked == [b"standard"]


def test_confirmation_and_history_show_the_chosen_option(client, first_product_id):
    confirmation = _checkout(client, first_product_id, fulfillment_option="pickup").data
    assert b"Store pickup" in confirmation
    assert b"Store pickup" in client.get("/orders").data
