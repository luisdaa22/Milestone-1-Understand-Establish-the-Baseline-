from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..db import get_session
from ..fulfillment import DEFAULT_OPTION, FULFILLMENT_OPTIONS, get_option
from ..models import Order, OrderItem
from ..payments import FakePaymentProcessor, PaymentDeclined
from .cart import get_cart_lines

bp = Blueprint("checkout", __name__, url_prefix="/checkout")


@bp.get("")
def checkout_form():
    db = get_session()
    lines = get_cart_lines(db)
    if not lines:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart.view_cart"))
    subtotal = sum(line.line_total_cents for line in lines)
    default_option = get_option(DEFAULT_OPTION)
    return render_template(
        "checkout.html",
        lines=lines,
        options=FULFILLMENT_OPTIONS,
        selected_option=default_option,
        subtotal_cents=subtotal,
        shipping_cents=default_option.price_cents,
        total_cents=subtotal + default_option.price_cents,
    )


@bp.post("")
def place_order():
    db = get_session()
    lines = get_cart_lines(db)
    if not lines:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart.view_cart"))

    option = get_option(request.form.get("fulfillment_option", DEFAULT_OPTION))
    if option is None:
        flash("Please choose a valid fulfillment option.", "error")
        return redirect(url_for("checkout.checkout_form"))

    customer_name = request.form.get("customer_name", "").strip()
    customer_email = request.form.get("customer_email", "").strip()
    shipping_address = request.form.get("shipping_address", "").strip()
    payment_token = request.form.get("payment_token", "").strip()

    if not option.requires_address:
        shipping_address = ""  # pickup orders are not shipped anywhere

    required = [customer_name, customer_email, payment_token]
    if option.requires_address:
        required.append(shipping_address)
    if not all(required):
        flash("Please complete all checkout fields.", "error")
        return redirect(url_for("checkout.checkout_form"))

    for line in lines:
        if line.quantity > line.product.stock_quantity:
            flash(f"Not enough stock for {line.product.name}.", "error")
            return redirect(url_for("cart.view_cart"))

    subtotal = sum(line.line_total_cents for line in lines)
    total = subtotal + option.price_cents

    try:
        payment_reference = FakePaymentProcessor().charge(total, payment_token)
    except PaymentDeclined:
        flash("Payment was declined. Try a different test token.", "error")
        return redirect(url_for("checkout.checkout_form"))

    order = Order(
        customer_name=customer_name,
        customer_email=customer_email,
        shipping_address=shipping_address,
        fulfillment_code=option.code,
        subtotal_cents=subtotal,
        shipping_cents=option.price_cents,
        total_cents=total,
        payment_reference=payment_reference,
        status="confirmed",
    )
    db.add(order)
    db.flush()

    for line in lines:
        order.items.append(
            OrderItem(
                product_id=line.product.id,
                sku=line.product.sku,
                product_name=line.product.name,
                unit_price_cents=line.product.price_cents,
                quantity=line.quantity,
            )
        )
        line.product.stock_quantity -= line.quantity

    db.commit()
    session["cart"] = {}
    flash("Order placed successfully.", "success")
    return redirect(url_for("orders.order_detail", order_id=order.id))
