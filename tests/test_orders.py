from sqlalchemy import select

from store.db import get_session
from store.models import Order, Product

CUSTOMER = {
    "customer_name": "Ada Lovelace",
    "customer_email": "ada@example.com",
    "shipping_address": "123 Analytical Engine Way",
    "payment_token": "tok_success",
}


def test_missing_order_returns_404(client):
    assert client.get("/orders/9999").status_code == 404


def test_order_keeps_price_after_product_price_changes(client, app, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    client.post("/checkout", data=CUSTOMER)
    with app.app_context():
        db = get_session()
        db.get(Product, first_product_id).price_cents = 99900
        db.commit()
    response = client.get("/orders/1")
    assert b"$100.00" in response.data
    assert b"$999.00" not in response.data


def test_order_history_lists_newest_first(client, app, first_product_id):
    for name in ("First Buyer", "Second Buyer"):
        client.post(f"/cart/add/{first_product_id}")
        client.post("/checkout", data={**CUSTOMER, "customer_name": name})
    page = client.get("/orders").data
    assert page.index(b"Second Buyer") < page.index(b"First Buyer")
    with app.app_context():
        assert len(get_session().scalars(select(Order)).all()) == 2


def test_checkout_order_defaults_to_standard_fulfillment(client, app, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    client.post("/checkout", data=CUSTOMER)
    with app.app_context():
        assert get_session().get(Order, 1).fulfillment_code == "standard"


def test_pickup_order_persists_without_shipping_address(app):
    with app.app_context():
        db = get_session()
        db.add(Order(
            customer_name="Ada Lovelace",
            customer_email="ada@example.com",
            shipping_address="",
            fulfillment_code="pickup",
            subtotal_cents=10000,
            shipping_cents=0,
            total_cents=10000,
            payment_reference="pay_test",
        ))
        db.commit()
    with app.app_context():
        order = get_session().scalar(select(Order))
        assert (order.fulfillment_code, order.shipping_address) == ("pickup", "")
