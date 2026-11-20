from sqlalchemy import func, select

from store.db import get_session
from store.models import Order

CUSTOMER = {
    "customer_name": "Ada Lovelace",
    "customer_email": "ada@example.com",
    "shipping_address": "123 Analytical Engine Way",
    "payment_token": "tok_success",
}


def _order_count(app):
    with app.app_context():
        return get_session().scalar(select(func.count()).select_from(Order))


def test_checkout_with_empty_cart_redirects_to_cart(client, app):
    assert b"Your cart is empty" in client.get("/checkout", follow_redirects=True).data
    assert b"Your cart is empty" in client.post("/checkout", data=CUSTOMER, follow_redirects=True).data
    assert _order_count(app) == 0


def test_checkout_with_missing_field_creates_no_order(client, app, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    data = {**CUSTOMER, "shipping_address": "  "}
    response = client.post("/checkout", data=data, follow_redirects=True)
    assert b"Please complete all checkout fields" in response.data
    assert _order_count(app) == 0


def test_order_total_includes_standard_shipping(client, app, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    client.post("/checkout", data=CUSTOMER)
    with app.app_context():
        order = get_session().scalar(select(Order))
        assert order.subtotal_cents == 10000
        assert order.shipping_cents == 9900
        assert order.total_cents == 19900


def test_successful_checkout_clears_cart(client, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    client.post("/checkout", data=CUSTOMER)
    assert b"Your cart is empty" in client.get("/cart").data
