from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Category, ProductReview, ProductAnswer
from django.core.paginator import Paginator
from orders.models import OrderItem   
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from coupons.models import Coupon
from django.utils import timezone
from datetime import datetime
from decimal import Decimal
from django.db.models.functions import Coalesce
from django.db.models import Case, When, Value, F, ExpressionWrapper, DecimalField, Count




def shop_view(request):
    """
    Shop page with dynamic sorting + pagination.
    Supported sort keys:
      - popularity (default)
      - low-to-high
      - high-to-low
      - rating
      - a-to-z
      - z-to-a
      - off-high
    """
    sort = request.GET.get('sort', 'popularity')
    page_number = request.GET.get('page', 1)

    # Base queryset: only available products
    qs = Product.objects.filter(is_available=True)

    # Effective price = discount_price (if exists) else price
    qs = qs.annotate(
        effective_price=Coalesce('discount_price', 'price')
    )

    # Average rating (for sorting by rating)
    qs = qs.annotate(
        avg_rating=Avg('reviews__rating')
    )

    # Discount % = ((price - effective_price) / price) * 100
    # When price is 0, keep 0 to avoid division error
    discount_percent_expr = Case(
        When(price__gt=0, then=ExpressionWrapper(
            ((F('price') - F('effective_price')) * 100.0) / F('price'),
            output_field=DecimalField(max_digits=6, decimal_places=2)
        )),
        default=Value(0),
        output_field=DecimalField(max_digits=6, decimal_places=2)
    )
    qs = qs.annotate(discount_percent=discount_percent_expr)

    # Apply sort
    if sort == 'low-to-high':
        qs = qs.order_by('effective_price', 'id')
    elif sort == 'high-to-low':
        qs = qs.order_by('-effective_price', 'id')
    elif sort == 'rating':
        qs = qs.order_by('-avg_rating', '-id')
    elif sort == 'a-to-z':
        qs = qs.order_by('title', 'id')
    elif sort == 'z-to-a':
        qs = qs.order_by('-title', 'id')
    elif sort == 'off-high':
        qs = qs.order_by('-discount_percent', '-id')
    else:
        # popularity proxy = latest products first
        qs = qs.order_by('-created_at', '-id')

    # Pagination (12 per page)
    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, 'shop.html', {
        'products': page_obj,   # page object (supports .has_next, .paginator, etc.)
        'categories': categories,
        'sort': sort,
    })


def category_view(request, parent_slug, child_slug=None):
    sort_option = request.GET.get('sort')
    page_number = request.GET.get('page')

    parent_category = get_object_or_404(Category, slug=parent_slug, parent=None)

    if child_slug:
        # Child Category Page
        category = get_object_or_404(Category, slug=child_slug, parent=parent_category)
        product_list = Product.objects.filter(category=category)

        if sort_option == 'low-to-high':
            product_list = product_list.order_by('discount_price')
        elif sort_option == 'high-to-low':
            product_list = product_list.order_by('-discount_price')

        paginator = Paginator(product_list, 8)
        page_obj = paginator.get_page(page_number)

        return render(request, 'category.html', {
            'category': category,
            'products': page_obj,             # Paged products
            'is_child': True,
            'sort_option': sort_option,
            'parent_products': None,          # Not used here
        })

    else:
        # Parent Category Page
        child_categories = Category.objects.filter(parent=parent_category)

        # Products under parent only (not children) — for listing & pagination
        parent_product_list = Product.objects.filter(category=parent_category)

        if sort_option == 'low-to-high':
            parent_product_list = parent_product_list.order_by('discount_price')
        elif sort_option == 'high-to-low':
            parent_product_list = parent_product_list.order_by('-discount_price')

        paginator = Paginator(parent_product_list, 8)
        page_obj = paginator.get_page(page_number)

        # All products under parent + children — only for slider
        all_categories = [parent_category] + list(child_categories)
        slider_products = Product.objects.filter(category__in=all_categories)

        return render(request, 'category.html', {
            'category': parent_category,
            'child_categories': child_categories,
            'products': page_obj,                # used in list section
            'parent_products': page_obj,         # also for condition check
            'is_child': False,
            'sort_option': sort_option,
            'slider_products': slider_products,  # optional if needed
        })

def product_detail_view(request, product_slug, category_slug=None, parent_slug=None, child_slug=None):
    if parent_slug and child_slug:
        # Case: /parent/child/product-slug/
        category = get_object_or_404(Category, slug=child_slug, parent__slug=parent_slug)
    elif category_slug:
        # Case: /parent/product-slug/
        category = get_object_or_404(Category, slug=category_slug, parent__isnull=True)
    else:
        # Fallback (shouldn't hit normally)
        category = None

    product = get_object_or_404(Product, slug=product_slug, category=category, is_available=True)

    # Related products
    related_products = Product.objects.filter(category=category).exclude(id=product.id)[:6]

    # ✅ Related reviews
    reviews = ProductReview.objects.filter(product=product)

    # ✅ Check if logged in and eligible to review
    has_purchased = False
    existing_review = None

    if request.user.is_authenticated:
        has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            product=product
        ).exists()

        existing_review = ProductReview.objects.filter(user=request.user, product=product).first()

        # ✅ Save or update review
        if request.method == 'POST' and has_purchased:
            rating = int(request.POST.get('rating'))
            comment = request.POST.get('comment')
            name = request.POST.get('name')

            if existing_review:
                existing_review.rating = rating
                existing_review.comment = comment
                existing_review.name = name
                existing_review.save()
            else:
                ProductReview.objects.create(
                    user=request.user,
                    product=product,
                    rating=rating,
                    comment=comment,
                    name=name
                )
            return redirect(request.path)
    rating_distribution = ProductReview.objects.filter(product=product).values('rating').annotate(count=Count('rating'))
    rating_dict = {r['rating']: r['count'] for r in rating_distribution}
    total_reviews = sum(rating_dict.values())

    average_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    # Filter only active, valid coupons for this product
    coupons = Coupon.objects.filter(
        active=True,
        public=True,
        valid_from__lte=timezone.now(),
        valid_to__gte=timezone.now(),
        applicable_products=product
    )

    # Annotate coupons with ₹ discount and sort by max discount
    coupon_data = []
    for coupon in coupons:
        off_amount = int(product.discount_price * (Decimal(coupon.discount_percent) / Decimal(100)))
        coupon_data.append({
            'name': coupon.name,
            'amount': off_amount,
            'code': coupon.code,
            'valid_to': coupon.valid_to.strftime("%d-%b-%Y"),
        })

    # Sort by rupee discount (descending)
    sorted_coupons = sorted(coupon_data, key=lambda x: x['amount'], reverse=True)
    visible_coupons = sorted(coupon_data, key=lambda x: x['amount'], reverse=True)[:2]

    answers = ProductAnswer.objects.filter(product=product).select_related('question')

    return render(request, 'shop-details.html', {
        'product': product,
        'related_products': related_products,
        'breadcrumb': category.__str__().split(" -> ") if category else [],
        'reviews': reviews,
        'can_review': has_purchased,
        'user_review': existing_review,
        'rating_dict': rating_dict,
        'total_reviews': total_reviews,
        'average_rating': average_rating,
        'coupons': sorted_coupons,
        'visible_coupons': visible_coupons,
        'answers': answers,
    })

@login_required
def review_submit(request, product_slug):
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=product_slug)
        rating = request.POST.get("rating")
        comment = request.POST.get("comment")
        name = request.POST.get("name")
        user = request.user

        # Check rating/comment before proceeding
        if not rating or not comment:
            return redirect(product.get_absolute_url())

        # Pehle object banao (rating/comment yahan pass mat karo)
        review, created = ProductReview.objects.get_or_create(user=user, product=product)

        # Ab rating aur comment set karo
        review.rating = int(rating)
        review.comment = comment
        review.name = name
        review.save()

        return redirect(product.get_absolute_url())

    return redirect('shop-page')