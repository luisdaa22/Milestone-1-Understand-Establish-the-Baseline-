"""Persistence and display of the chosen fulfillment option (Milestone 2)."""
from sqlalchemy import func, select

from store.db import get_session
from store.models import Order, Product

CUSTOMER = {
    "customer_name": "Ada Lovelace",
    "customer_email": "ada@example.com",
    "shipping_address": "123 Analytical Engine Way",
    "payment_token": "tok_success",
}


def _checkout(client, product_id, **form):
    client.post(f"/cart/add/{product_id}")
    return client.post("/checkout", data={**CUSTOMER, **form}, follow_redirects=True)


def _order_count(app):
    with app.app_context():
        return get_session().scalar(select(func.count()).select_from(Order))


def _stock(app, product_id):
    with app.app_context():
        return get_session().get(Product, product_id).stock_quantity


def test_order_created_without_code_defaults_to_standard(app):
    with app.app_context():
        db = get_session()
        db.add(Order(customer_name="Legacy", customer_email="legacy@example.com", shipping_address="Old St 1",
                     subtotal_cents=10_000, shipping_cents=9_900, total_cents=19_900, payment_reference="pay_legacy"))
        db.commit()
        assert db.scalar(select(Order)).fulfillment_code == "standard"


def test_order_with_retired_option_still_renders_its_code(client, app):
    with app.app_context():
        db = get_session()
        db.add(Order(customer_name="Old Buyer", customer_email="old@example.com", shipping_address="Old St 1",
                     fulfillment_code="same_day", subtotal_cents=10_000, shipping_cents=14_900, total_cents=24_900,
                     payment_reference="pay_old"))
        db.commit()
    assert b"same_day" in client.get("/orders").data
    detail = client.get("/orders/1")
    assert detail.status_code == 200
    assert b"same_day" in detail.data


def test_shipping_confirmation_shows_label_and_address(client, first_product_id):
    page = _checkout(client, first_product_id, fulfillment_option="express").data
    assert b"Express shipping" in page
    assert b"123 Analytical Engine Way" in page
    assert b"no shipping address" not in page


def test_pickup_confirmation_says_there_is_no_address(client, first_product_id):
    page = _checkout(client, first_product_id, fulfillment_option="pickup").data
    assert b"Pick up in store" in page


def test_history_shows_each_order_with_its_own_option(client, first_product_id):
    for code in ("standard", "express", "pickup"):
        _checkout(client, first_product_id, fulfillment_option=code)
    page = client.get("/orders").data
    for label in (b"Standard shipping", b"Express shipping", b"Store pickup"):
        assert page.count(label) == 1


def test_express_with_insufficient_stock_is_rejected(client, app, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    client.post(f"/cart/update/{first_product_id}", data={"quantity": "8"})
    response = client.post("/checkout", data={**CUSTOMER, "fulfillment_option": "express"}, follow_redirects=True)
    assert b"Not enough stock" in response.data
    assert _order_count(app) == 0
    assert _stock(app, first_product_id) == 5


def test_declined_pickup_keeps_stock_and_creates_no_order(client, app, first_product_id):
    response = _checkout(client, first_product_id, fulfillment_option="pickup", payment_token="tok_fail")
    assert b"Payment was declined" in response.data
    assert _order_count(app) == 0
    assert _stock(app, first_product_id) == 5


def test_checkout_page_starts_with_standard_total(client, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    page = client.get("/checkout").data
    assert b'id="shipping-amount">$99.00' in page
    assert b'id="total-amount">$199.00' in page
