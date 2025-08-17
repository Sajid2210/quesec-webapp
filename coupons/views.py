from django.shortcuts import redirect, render
from .models import Coupon
from bicycles.models import Product 
from django.utils import timezone

def apply_coupon(request):
    code = request.GET.get('code')
    now = timezone.now()

    try:
        coupon = Coupon.objects.get(code__iexact=code, valid_from__lte=now, valid_to__gte=now, active=True)

        # Get cart
        cart = request.session.get('cart', {})
        product_ids = [int(pid) for pid in cart.keys()]
        cart_products = Product.objects.filter(id__in=product_ids)

        # If coupon is restricted to specific products
        if coupon.applicable_products.exists():
            matched_products = coupon.applicable_products.filter(id__in=product_ids)

            if not matched_products.exists():
                # No matching product — invalid coupon
                request.session['coupon_code'] = None
                request.session['coupon_discount'] = 0
                request.session['coupon_product_ids'] = []  # optional: clear
                return redirect('view_cart')

            # ✅ Valid: store matched product IDs for partial discount
            request.session['coupon_product_ids'] = list(matched_products.values_list('id', flat=True))
        else:
            # ✅ Apply to all products if no specific filter
            request.session['coupon_product_ids'] = product_ids

        # ✅ Only one active coupon at a time — overwrite previous
        request.session['coupon_code'] = coupon.code
        request.session['coupon_discount'] = coupon.discount_percent

    except Coupon.DoesNotExist:
        request.session['coupon_code'] = None
        request.session['coupon_discount'] = 0
        request.session['coupon_product_ids'] = []

    return redirect('view_cart')

def remove_coupon(request):
    # Step 1: Remove coupon from session
    request.session.pop('coupon_code', None)
    request.session.pop('coupon_discount', None)
    request.session.pop('coupon_product_ids', None)

    # Step 2: Get cart from session
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = 0
    cart_total = 0
    product_discount = 0
    shipping_total = 0
    discount_amount = 0

    for product_id, qty in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            item_total = product.discount_price * qty
            item_cart_total = product.price * qty
            item_product_discount = (product.price - product.discount_price) * qty
            item_shipping = product.shipping_charge * qty

            cart_items.append({
                'product': product,
                'qty': qty,
                'subtotal': item_total,
                'cart_total': item_cart_total,
                'product_discount': item_product_discount,
                'shipping': item_shipping,
                'discount': 0,  # no coupon now
            })

            subtotal += item_total
            cart_total += item_cart_total
            product_discount += item_product_discount
            shipping_total += item_shipping

        except Product.DoesNotExist:
            continue

    # Free shipping above ₹5000
    if subtotal >= 5000:
        shipping_total = 0

    final_total = subtotal + shipping_total

    # Active coupons for modal
    product_ids = list(map(int, cart.keys()))
    active_coupons = Coupon.objects.filter(
        active=True,
        public=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now(),
        applicable_products__id__in=product_ids
    ).distinct().order_by('-discount_percent')

    context = {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'product_discount': product_discount,
        'subtotal': subtotal,
        'shipping_total': shipping_total,
        'discount_amount': discount_amount,
        'total': final_total,
        'active_coupons': active_coupons,
        'cart_product_ids': product_ids,
    }

    return render(request, 'cart.html', context)