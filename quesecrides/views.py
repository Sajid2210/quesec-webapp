from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from bicycles.models import Product
from django.utils.timezone import now
from coupons.models import Coupon
from django.conf import settings



def home(request):
    return render(request, 'index.html')

def custom_page_not_found(request, exception):
    return render(request, '404.html', status=404)

def custom_server_error(request):
    # templates/500.html required
    return render(request, "500.html", status=500)

def add_to_cart(request, product_id):
    print("Product ID Received:", product_id)
    try:
        product = Product.objects.get(id=product_id)
        print("Product Found:", product.title)

        cart = request.session.get('cart', {})
        if str(product_id) in cart:
            return redirect('view_cart')

        cart[str(product_id)] = 1
        request.session['cart'] = cart

        return redirect('view_cart')  # ✅ this is what was missing
    except Product.DoesNotExist:
        print("Product with ID does not exist:", product_id)
        return redirect('shop-page')

def view_cart(request):
    cart = request.session.get('cart', {})
    # ✅ If cart is empty, clear coupon info from session
    if not cart:
        request.session.pop('coupon_code', None)
        request.session.pop('coupon_discount', None)
        request.session.pop('coupon_product_ids', None)
    cart_items = []
    subtotal = 0
    cart_total = 0
    product_discount = 0
    discount_amount = 0
    shipping_total = 0

    coupon_code = request.session.get('coupon_code')
    coupon_discount = request.session.get('coupon_discount', 0)
    coupon_product_ids = request.session.get('coupon_product_ids', [])

    for product_id, qty in cart.items():
        product = get_object_or_404(Product, id=product_id)
        cart_price_total = product.price * qty
        cart_total += cart_price_total
        item_total = product.discount_price * qty
        subtotal += item_total
        product_discount = cart_total - subtotal

        shipping_total += product.shipping_charge * qty

        # ✅ Apply discount only if product is eligible
        if int(product_id) in coupon_product_ids:
            item_discount = item_total * coupon_discount / 100
            discount_amount += item_discount
        else:
            item_discount = 0

        cart_items.append({
            'product': product,
            'qty': qty,
            'subtotal': item_total,
            'cart_total': cart_price_total,
            'product_discount': product_discount,
            'discount': item_discount,
        })

    # ✅ Free shipping above ₹5000
    if subtotal >= 5000:
        shipping_total = 0

    final_total = subtotal - discount_amount + shipping_total

    # ✅ Get active coupons
    product_ids = list(map(int, cart.keys()))
    active_coupons = Coupon.objects.filter(
        active=True,
        public=True,
        valid_from__lte=now(),
        valid_to__gte=now(),
        applicable_products__id__in=product_ids
    ).distinct().order_by('-discount_percent')
    cart_product_ids = list(map(int, cart.keys()))

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'cart_total': cart_total,
        'product_discount': product_discount,
        'coupon_code': coupon_code,
        'coupon_discount': coupon_discount,
        'discount_amount': discount_amount,
        'shipping_total': shipping_total,
        'total': final_total,
        'active_coupons': active_coupons,
        'cart_product_ids': cart_product_ids,
    }

    return render(request, 'cart.html', context)

def update_qty(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_qty = int(request.POST.get('qty'))

        cart = request.session.get('cart', {})

        if product_id in cart:
            if new_qty <= 0:
                del cart[product_id]
            else:
                cart[product_id] = new_qty
            request.session['cart'] = cart

        # Recalculate totals
        cart_items = []
        subtotal = 0
        discount_amount = 0
        cart_total = 0
        product_discount = 0
        shipping_total = 0
        coupon_code = request.session.get('coupon_code')
        coupon_discount = request.session.get('coupon_discount', 0)
        coupon_product_ids = request.session.get('coupon_product_ids', [])

        for pid, qty in cart.items():
            product = get_object_or_404(Product, id=pid)
            cart_price_total = product.price * qty
            cart_total += cart_price_total
            item_total = product.discount_price * qty
            subtotal += item_total
            product_discount = cart_total - subtotal
            shipping_total += product.shipping_charge * qty

            if int(pid) in coupon_product_ids:
                item_discount = item_total * coupon_discount / 100
                discount_amount += item_discount

        # ✅ Free shipping above ₹5000
        if subtotal >= 5000:
            shipping_total = 0

        final_total = subtotal - discount_amount + shipping_total
        request.session.pop('coupon_code', None)
        request.session.pop('coupon_discount', None)

        return JsonResponse({
            'success': True,
            'subtotal': f"{subtotal:.2f}",
            'discount': f"{discount_amount:.2f}",
            'total': f"{final_total:.2f}",
            'cart_total': f"{cart_total:.2f}",               
            'product_discount': f"{product_discount:.2f}",
            'shipping': f"{shipping_total:.2f}",
        })

    return JsonResponse({'success': False})

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart

    return redirect('view_cart')

def checkout_page(request):
    cart = request.session.get('cart', {})

    # ✅ Redirect if cart is empty
    if not cart:
        return redirect('home')

    cart_items = []
    subtotal = 0
    cart_total = 0
    product_discount = 0
    discount_amount = 0
    shipping_total = 0

    coupon_code = request.session.get('coupon_code')
    coupon_discount = request.session.get('coupon_discount', 0)
    coupon_product_ids = request.session.get('coupon_product_ids', [])

    for product_id, qty in cart.items():
        product = get_object_or_404(Product, id=product_id)
        cart_price_total = product.price * qty
        cart_total += cart_price_total
        item_total = product.discount_price * qty
        item_price = product.price * qty
        subtotal += item_total
        product_discount = cart_total - subtotal

        shipping_total += product.shipping_charge * qty

        if int(product_id) in coupon_product_ids:
            item_discount = item_total * coupon_discount / 100
            discount_amount += item_discount

        cart_items.append({
            'product': product,
            'qty': qty,
            'subtotal': item_total,
            'product_total_price': item_price,
        })

    if subtotal >= 5000:
        shipping_total = 0

    final_total = subtotal - discount_amount + shipping_total

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'cart_total': cart_total,
        'product_discount': product_discount,
        'coupon_code': coupon_code,
        'coupon_discount': coupon_discount,
        'discount_amount': discount_amount,
        'shipping_total': shipping_total,
        'total': final_total,
        'razorpay_key': settings.RAZORPAY_KEY, 
    }

    return render(request, 'checkout.html', context)


    
