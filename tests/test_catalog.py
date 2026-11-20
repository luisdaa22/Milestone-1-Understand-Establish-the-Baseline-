def test_catalog_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"First Product" in response.data
    assert b"Second Product" in response.data


def test_product_detail_loads(client, first_product_id):
    response = client.get(f"/products/{first_product_id}")
    assert response.status_code == 200
    assert b"First Product" in response.data


def test_missing_product_returns_404(client):
    assert client.get("/products/9999").status_code == 404


def _deactivate(app, product_id):
    from store.db import get_session
    from store.models import Product
    with app.app_context():
        db = get_session()
        db.get(Product, product_id).active = 0
        db.commit()


def test_inactive_product_is_hidden_from_catalog(client, app, first_product_id):
    _deactivate(app, first_product_id)
    response = client.get("/")
    assert b"First Product" not in response.data
    assert b"Second Product" in response.data


def test_inactive_product_detail_returns_404(client, app, first_product_id):
    _deactivate(app, first_product_id)
    assert client.get(f"/products/{first_product_id}").status_code == 404
