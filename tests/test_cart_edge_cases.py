def test_add_missing_product_shows_error(client):
    response = client.post("/cart/add/9999", follow_redirects=True)
    assert b"Product not found" in response.data
    assert b"Your cart is empty" in client.get("/cart").data


def test_adding_same_product_twice_increments_quantity(client, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    client.post(f"/cart/add/{first_product_id}")
    response = client.get("/cart")
    assert b'value="2"' in response.data
    assert b"$200.00" in response.data


def test_update_to_zero_removes_line(client, first_product_id):
    client.post(f"/cart/add/{first_product_id}")
    client.post(f"/cart/update/{first_product_id}", data={"quantity": "0"})
    assert b"Your cart is empty" in client.get("/cart").data
