from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import CartLead
from bicycles.models import Product

@csrf_exempt
def save_checkout_lead(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        name = request.POST.get('name', '')
        cart = request.session.get('cart', {})

        if not phone:
            return JsonResponse({'status': 'phone_required'})

        # Build readable cart summary
        product_list = []
        for product_id, qty in cart.items():
            try:
                product = Product.objects.get(id=int(product_id))
                product_list.append(f"{product.title} (Qty: {qty})")
            except Product.DoesNotExist:
                continue

        cart_summary = "\n".join(product_list)

        # Avoid duplicates: if same phone already exists, skip
        if not CartLead.objects.filter(phone=phone).exists():
            CartLead.objects.create(
                name=name,
                phone=phone,
                cart_items=cart_summary
            )
            return JsonResponse({'status': 'saved'})
        else:
            return JsonResponse({'status': 'already_exists'})

    return JsonResponse({'status': 'invalid_request'})