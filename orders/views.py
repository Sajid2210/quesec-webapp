from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, Http404
from decimal import Decimal
from django.contrib import messages
from .models import Order, OrderItem
from bicycles.models import Product
from django.views.decorators.csrf import csrf_exempt
from accounts.models import CustomUser
from django.contrib.auth import login
from cartwatch.models import CartLead
import hashlib
import random
import string
from django.urls import reverse
from django.conf import settings

# ---------------- Helpers ----------------

def _txnid():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def _safe_float(val, default=0.0):
    try:
        return float(val or 0)
    except Exception:
        return float(default)

def _cart_snapshot(request):
    """
    Session cart -> list of {product, qty}
    String keys ko int me coerce karta hai; missing products skip.
    """
    snap = []
    cart = request.session.get("cart", {}) or {}
    for pid, qty in cart.items():
        try:
            p = Product.objects.get(id=int(pid))
            snap.append((p, int(qty)))
        except Product.DoesNotExist:
            continue
    return snap

def _create_order_items(order, snap):
    """ Given a snapshot (product, qty) list, persist OrderItem rows. """
    for p, qty in snap:
        OrderItem.objects.create(order=order, product=p, quantity=max(int(qty), 1))

# ---------------- Save order (Razorpay/COD etc.) ----------------

@csrf_exempt
def save_order(request):
    if request.method != 'POST':
        return redirect('shop-page')

    snap = _cart_snapshot(request)
    if not snap:
        return redirect('shop-page')

    # totals (discount already applied frontend me; yahan simplified)
    subtotal = sum(p.discount_price * qty for p, qty in snap)
    coupon_code = request.session.get('coupon_code')
    coupon_discount = int(request.session.get('coupon_discount', 0))
    discount_amount = subtotal * coupon_discount / 100
    total = subtotal - discount_amount

    # user
    email = request.POST.get('email')
    user = CustomUser.objects.filter(email=email).first()
    if not user:
        user = CustomUser.objects.create_user(email=email)
    login(request, user)

    # lead cleanup
    phone = request.POST.get('phone')
    if phone:
        CartLead.objects.filter(phone=phone).delete()

    # order
    order = Order.objects.create(
        name=request.POST.get('name'),
        phone=phone,
        email=email,
        address=request.POST.get('address'),
        city=request.POST.get('city'),
        state=request.POST.get('state'),
        pincode=request.POST.get('pincode'),
        company=request.POST.get('company'),
        gst=request.POST.get('gst'),
        payment_method=request.POST.get('payment_method'),
        transaction_id=request.POST.get('transaction_id'),
        total_amount=float(total),
        coupon_code=coupon_code,
        coupon_discount=coupon_discount,
        user=user,
    )

    # items -> persist immediately ✅
    _create_order_items(order, snap)

    # clear cart but remember order for thank-you access ✅
    request.session['cart'] = {}
    request.session['coupon_code'] = None
    request.session['coupon_discount'] = 0
    request.session['coupon_product_ids'] = []
    request.session['last_order_id'] = order.id
    request.session.modified = True

    return redirect(f"{reverse('thank_you')}?order_id={order.id}")

# ---------------- PayU Initiate (Full) ----------------

@csrf_exempt
def payu_initiate(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    snap = _cart_snapshot(request)
    if not snap:
        return HttpResponseBadRequest("Cart is empty.")

    subtotal = sum(p.discount_price * qty for p, qty in snap)
    coupon_discount = int(request.session.get('coupon_discount', 0))
    discount_amount = subtotal * coupon_discount / 100
    final_total = subtotal - discount_amount
    amount_str = f"{final_total:.2f}"

    # customer info
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    address = request.POST.get("address", "").strip()
    pincode = request.POST.get("pincode", "").strip()
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()

    txnid = _txnid()
    order = Order.objects.create(
        name=name, email=email, phone=phone,
        address=address, pincode=pincode, city=city, state=state,
        total_amount=float(final_total), payment_method="payu",
        payment_status="Pending", transaction_id=txnid,
        coupon_code=request.session.get('coupon_code'),
        coupon_discount=coupon_discount,
    )

    # ✅ Persist items RIGHT NOW so success me session na bhi mile to items rahen
    _create_order_items(order, snap)

    # remember last order id (fresh flow ke liye)
    request.session['last_order_id'] = order.id
    request.session.modified = True

    key = settings.PAYU_MERCHANT_KEY
    salt = settings.PAYU_MERCHANT_SALT
    productinfo = f"Order_{order.id}"
    surl = request.build_absolute_uri(reverse("payu-success"))
    furl = request.build_absolute_uri(reverse("payu-failure"))

    hash_string = f"{key}|{txnid}|{amount_str}|{productinfo}|{name}|{email}|||||||||||{salt}"
    payu_hash = hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()

    return render(request, "payu_redirect.html", {
        "payu_url": settings.PAYU_BASE_URL,
        "payu_key": key,
        "txnid": txnid,
        "amount": amount_str,
        "productinfo": productinfo,
        "name": name, "email": email, "phone": phone,
        "surl": surl, "furl": furl, "payu_hash": payu_hash
    })

# ---------------- PayU Initiate (UPI-only) ----------------

@csrf_exempt
def payu_initiate_upi(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    snap = _cart_snapshot(request)
    if not snap:
        return HttpResponseBadRequest("Cart is empty.")

    subtotal = sum(p.discount_price * qty for p, qty in snap)
    coupon_discount = int(request.session.get('coupon_discount', 0))
    discount_amount = subtotal * coupon_discount / 100
    final_total = subtotal - discount_amount
    amount_str = f"{final_total:.2f}"

    # customer
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    address = request.POST.get("address", "").strip()
    pincode = request.POST.get("pincode", "").strip()
    city = request.POST.get("city", "").strip()
    state = request.POST.get("state", "").strip()

    txnid = _txnid()
    order = Order.objects.create(
        name=name, email=email, phone=phone,
        address=address, pincode=pincode, city=city, state=state,
        total_amount=float(final_total), payment_method="payu_upi",
        payment_status="Pending", transaction_id=txnid,
        coupon_code=request.session.get('coupon_code'),
        coupon_discount=coupon_discount,
    )

    # ✅ Persist items at initiate
    _create_order_items(order, snap)

    request.session['last_order_id'] = order.id
    request.session.modified = True

    key = settings.PAYU_MERCHANT_KEY
    salt = settings.PAYU_MERCHANT_SALT
    productinfo = f"Order_{order.id}"
    surl = request.build_absolute_uri(reverse("payu-success"))
    furl = request.build_absolute_uri(reverse("payu-failure"))

    hash_string = f"{key}|{txnid}|{amount_str}|{productinfo}|{name}|{email}|||||||||||{salt}"
    payu_hash = hashlib.sha512(hash_string.encode("utf-8")).hexdigest().lower()

    context = {
        "payu_url": settings.PAYU_BASE_URL,
        "payu_key": key,
        "txnid": txnid,
        "amount": amount_str,
        "productinfo": productinfo,
        "name": name, "email": email, "phone": phone,
        "surl": surl, "furl": furl, "payu_hash": payu_hash,
        "pg": "UPI", "bankcode": "UPI", "enforce_paymethod": "upi",
    }
    return render(request, "payu_upi_redirect.html", context)

# ---------------- PayU Success / Failure ----------------

@csrf_exempt
def payu_success(request):
    data = request.POST
    status = data.get("status")
    txnid = data.get("txnid")
    hash_received = data.get("hash")
    paid_amount_str = data.get("amount")

    key = settings.PAYU_MERCHANT_KEY
    salt = settings.PAYU_MERCHANT_SALT

    try:
        order = Order.objects.prefetch_related("items__product").get(transaction_id=txnid)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect("shop-page")

    # verify hash
    verify_seq = f"{salt}|{status}|||||||||||{data.get('email')}|{data.get('firstname')}|{data.get('productinfo')}|{paid_amount_str}|{txnid}|{key}"
    expected = hashlib.sha512(verify_seq.encode("utf-8")).hexdigest().lower()
    if hash_received != expected:
        order.payment_status = "Failed"; order.save()
        messages.error(request, "Payment verification failed.")
        return redirect("shop-page")

    # amount check
    if Decimal(paid_amount_str).quantize(Decimal("0.01")) != \
       Decimal(str(order.total_amount)).quantize(Decimal("0.01")):
        order.payment_status = "Failed"; order.save()
        messages.error(request, "Amount mismatch. Order flagged.")
        return redirect("shop-page")

    # login/create user if we have email
    if order.email:
        user = CustomUser.objects.filter(email=order.email).first()
        if not user:
            user = CustomUser.objects.create_user(email=order.email)
        try:
            login(request, user)
        except Exception:
            pass
        order.user = user

    # safety net: if, for any reason, items are missing, try from current session snap
    if not order.items.exists():
        snap = _cart_snapshot(request)
        if snap:
            _create_order_items(order, snap)

    # cleanup + mark paid
    if order.phone:
        CartLead.objects.filter(phone=order.phone).delete()
    order.payment_status = "Paid"
    order.save()

    # clear session but keep last order id
    request.session['cart'] = {}
    request.session['coupon_code'] = None
    request.session['coupon_discount'] = 0
    request.session['coupon_product_ids'] = []
    request.session['last_order_id'] = order.id
    request.session.modified = True

    messages.success(request, "Payment successful! Thank you for your order.")
    return redirect(f"{reverse('thank_you')}?order_id={order.id}")

@csrf_exempt
def payu_failure(request):
    data = request.POST
    txnid = data.get("txnid")
    try:
        order = Order.objects.get(transaction_id=txnid)
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
        return redirect("shop-page")
    order.payment_status = "Failed"
    order.save()
    messages.error(request, "Payment failed. Please try again.")
    return redirect("checkout-page")

# ---------------- Secure Thank‑You ----------------

PAYMENT_LABELS = {
    "full": "Razorpay Full",
    "cod": "COD with 20% Advance",
    "payu": "PayU Full",
    "payu_upi": "PayU UPI",
}

def thank_you(request):
    """
    Secure Thank‑You:
      allow if staff OR order.user==request.user OR same session (last_order_id).
      else -> 404 (to avoid information leak).
    """
    order_id = request.GET.get("order_id") or request.GET.get("order") or request.session.get("last_order_id")

    try:
        order = Order.objects.prefetch_related("items__product").get(pk=order_id)
    except Exception:
        order = None

    if not order:
        return render(request, "thank_you.html", {"order": None})

    allowed = False
    if request.user.is_staff:
        allowed = True
    elif order.user_id:
        if request.user.is_authenticated and request.user.id == order.user_id:
            allowed = True
    else:
        if request.session.get("last_order_id") == order.id:
            allowed = True

    if not allowed:
        raise Http404("Order not found")

    # build items for template
    items = []
    subtotal = 0.0
    for oi in order.items.all():
        p = oi.product
        qty = int(getattr(oi, "quantity", 1))
        price = _safe_float(getattr(p, "discount_price", None) or getattr(p, "price", 0))
        line_total = price * qty
        subtotal += line_total
        try:
            image_url = p.image.url if getattr(p, "image", None) else None
        except Exception:
            image_url = None
        items.append({
            "title": getattr(p, "title", "Product"),
            "sku": getattr(p, "sku", None),
            "image": image_url,
            "qty": qty,
            "price": price,
            "total": line_total,
        })

    coupon_percent = int(order.coupon_discount or 0)
    coupon_value = round(subtotal * (coupon_percent / 100.0), 2)

    grand_total = _safe_float(order.total_amount)
    shipping_total = grand_total - max(subtotal - coupon_value, 0)
    if shipping_total < 0:
        shipping_total = 0.0

    advance_amount = 0.0
    if order.payment_method == "cod":
        advance_amount = round(grand_total * 0.20, 2)

    totals = {
        "subtotal": round(subtotal, 2),
        "coupon_value": round(coupon_value, 2),
        "shipping_total": round(shipping_total, 2),
        "advance_amount": advance_amount,
    }

    payment_label = PAYMENT_LABELS.get(order.payment_method, order.payment_method)

    return render(request, "thank_you.html", {
        "order": order,
        "items": items,
        "totals": totals,
        "payment_label": payment_label,
    })
