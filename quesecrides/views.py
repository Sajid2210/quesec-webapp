# /quesecrides/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.conf import settings
from bicycles.models import Product
from coupons.models import Coupon

# -----------------------------
# Helpers
# -----------------------------
def _get_cart(request):
    """
    Session cart structure:
    request.session['cart'] = {
        "<product_id>": <qty:int>
    }
    """
    cart = request.session.get('cart', {})
    # normalize keys to str and qty to int
    normalized = {}
    for k, v in cart.items():
        try:
            qty = int(v)
        except (TypeError, ValueError):
            qty = 1
        normalized[str(k)] = max(1, qty)
    request.session['cart'] = normalized
    return normalized

def _compute_totals(request, cart):
    """
    Returns dict with all totals the templates expect.
    - Uses Product.price and Product.discount_price
    - Applies coupon stored in session (percentage) **only** on applicable product ids
    - Free shipping for subtotal >= 5000
    """
    cart_items = []
    subtotal = 0
    cart_total = 0
    shipping_total = 199  # default shipping; will be zeroed on threshold
    product_discount = 0  # price - discount_price total
    discount_amount = 0

    # coupon session info
    coupon_code = request.session.get('coupon_code')
    coupon_discount = float(request.session.get('coupon_discount', 0))  # percentage like 10 for 10%
    coupon_product_ids = set(str(x) for x in request.session.get('coupon_product_ids', []))

    # build items
    for product_id, qty in cart.items():
        product = get_object_or_404(Product, id=product_id)
        qty = int(qty)

        # guard for missing discount_price
        item_price = float(product.price or 0) * qty
        item_discount_price = float(product.discount_price or product.price or 0) * qty

        cart_total += item_price
        subtotal += item_discount_price
        product_discount = cart_total - subtotal

        cart_items.append({
            "product": product,
            "qty": qty,
            "subtotal": item_discount_price,        # discounted subtotal for this line
            "product_total_price": item_price,      # MRP subtotal for this line
        })

    # coupon calculation (percentage on eligible items)
    if coupon_code and coupon_discount > 0:
        eligible_subtotal = 0.0
        if coupon_product_ids:
            # only selected products
            for product_id, qty in cart.items():
                if str(product_id) in coupon_product_ids:
                    p = get_object_or_404(Product, id=product_id)
                    eligible_subtotal += float(p.discount_price or p.price or 0) * int(qty)
        else:
            # all products
            eligible_subtotal = float(subtotal)

        discount_amount = round((eligible_subtotal * (coupon_discount / 100.0)), 2)

    # shipping free over threshold
    if subtotal >= 5000:
        shipping_total = 0

    final_total = round(subtotal - discount_amount + shipping_total, 2)

    return {
        "cart_items": cart_items,
        "subtotal": round(subtotal, 2),
        "cart_total": round(cart_total, 2),
        "product_discount": round(product_discount, 2),
        "coupon_code": coupon_code,
        "coupon_discount": coupon_discount,
        "discount_amount": round(discount_amount, 2),
        "shipping_total": shipping_total,
        "total": final_total,
    }

# -----------------------------
# Pages / Views
# -----------------------------
def home(request):
    return render(request, "index.html")

def custom_page_not_found(request, exception):
    return render(request, "404.html", status=404)

def custom_server_error(request):
    # optional: show a simple page
    return render(request, "500.html", status=500)

# ---- CART ----
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)  # ensure exists
    cart = _get_cart(request)
    cart[str(product.id)] = cart.get(str(product.id), 0) + 1
    request.session["cart"] = cart
    return redirect("view_cart")

def remove_from_cart(request, product_id):
    cart = _get_cart(request)
    pid = str(product_id)
    if pid in cart:
        del cart[pid]
        request.session["cart"] = cart
    return redirect("view_cart")

def view_cart(request):
    cart = _get_cart(request)
    # If cart empty, clear coupon session
    if not cart:
        request.session.pop("coupon_code", None)
        request.session.pop("coupon_discount", None)
        request.session.pop("coupon_product_ids", None)

    totals = _compute_totals(request, cart)
    context = {**totals}
    return render(request, "cart.html", context)

def update_qty(request):
    """
    Ajax or form POST to update line quantities,
    then render checkout again (same totals variables).
    """
    if request.method == "POST":
        product_id = str(request.POST.get("product_id"))
        try:
            new_qty = int(request.POST.get("qty", 1))
        except (TypeError, ValueError):
            new_qty = 1

        cart = _get_cart(request)
        if product_id in cart:
            if new_qty <= 0:
                del cart[product_id]
            else:
                cart[product_id] = new_qty
            request.session["cart"] = cart

    totals = _compute_totals(request, _get_cart(request))
    context = {**totals, "razorpay_key": getattr(settings, "RAZORPAY_KEY", "")}
    return render(request, "checkout.html", context)

# ---- CHECKOUT ----
def checkout_page(request):
    cart = _get_cart(request)
    # redirect if empty
    if not cart:
        return redirect("home")

    totals = _compute_totals(request, cart)

    context = {
        **totals,
        "razorpay_key": getattr(settings, "RAZORPAY_KEY", ""),
    }
    return render(request, "checkout.html", context)
