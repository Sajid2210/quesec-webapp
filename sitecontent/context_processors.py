from .models import SiteSettings, NavMenu, FtNavMenu1, FtNavMenu2, FtNavMenu3, CatMenu, Hero, HeroTwo, CouponCodeOffer
from bicycles.models import Category, Product
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

from .models import (
    SiteSettings, NavMenu, FtNavMenu1, FtNavMenu2, FtNavMenu3,
    CatMenu, Hero, HeroTwo, CouponCodeOffer, BestSellerBlock, HomeCategorySection
)

# NOTE: Make sure these app/model paths match your project
from bicycles.models import Category, Product
from orders.models import OrderItem

from blog.models import BlogPost


def site_info(request):
    """Basic site-wide objects for header/footer and hero banners."""
    settings = SiteSettings.objects.first()

    home_blog_posts = (
        BlogPost.objects.filter(status="published")
        .select_related("category")
        .order_by("-published_at", "-created_at")[:6]
    )


    return {
        "site_settings": settings,
        "nav_menus": NavMenu.objects.all(),
        "ft_nav1": FtNavMenu1.objects.all(),
        "ft_nav2": FtNavMenu2.objects.all(),
        "ft_nav3": FtNavMenu3.objects.all(),
        "cat_nav3": CatMenu.objects.all(),
        "hero_banner": Hero.objects.first(),
        "hero_two_banner": HeroTwo.objects.first(),
        "coupon_offers": CouponCodeOffer.objects.all(),
        "home_blog_posts": home_blog_posts,
    }

def _collect_descendant_ids(root_qs):
    """
    Given a queryset of Category objects, return a set of IDs including the roots
    and ALL their descendants (multi-level).
    """
    to_visit = list(root_qs.values_list('id', flat=True))
    seen = set(to_visit)

    while to_visit:
        child_ids = list(Category.objects.filter(parent_id__in=to_visit)
                         .values_list('id', flat=True))
        new_ids = [cid for cid in child_ids if cid not in seen]
        if not new_ids:
            break
        seen.update(new_ids)
        to_visit = new_ids

    return seen


def get_total_products(category):
    """
    Total products under this category including ALL descendants (not just one level).
    """
    # Start from this category as a queryset
    roots = Category.objects.filter(id=category.id)
    all_ids = _collect_descendant_ids(roots)
    return Product.objects.filter(category_id__in=list(all_ids)).count()

def shop_categories(request):
    """
    Build the category boxes with total counts including descendants.
    Also include the category's full URL (handles parent/child slug pattern).
    """
    categories_to_show = []
    all_categories = Category.objects.all().prefetch_related('children')

    for category in all_categories:
        total = get_total_products(category)
        if total > 0:
            categories_to_show.append({
                'name': category.name,
                'slug': category.slug,
                'image': category.image.url if category.image else '',
                'total_products': total,
                'url': category.get_absolute_url(),  # ✅ add full URL for template
            })

    return {'shop_categories': categories_to_show}

def best_seller_bicycles(request):
    """
    BEST SELLERS (Admin-controlled via BestSellerBlock singleton)
    - Picks the ONLY BestSellerBlock instance (if present)
    - Uses selected categories + ALL their descendants
    - Optionally limits by last N days (days_window)
    - Ranks by total quantity sold (OrderItem.quantity)
    """
    block = BestSellerBlock.objects.first()
    if not block:
        # No block configured yet -> return empty but safe context
        return {
            "best_seller_bicycles": [],
            "best_seller_block": None,
        }

    selected_cats = block.categories.all()
    if not selected_cats.exists():
        # Block present but no categories picked
        return {
            "best_seller_bicycles": [],
            "best_seller_block": block,
        }

    # Collect selected categories + all descendants
    all_cat_ids = _collect_descendant_ids(selected_cats)
    # Also include selected root ids explicitly
    all_cat_ids.update(selected_cats.values_list("id", flat=True))

    # Base queryset: products in any of those categories that have at least one orderitem
    qs = Product.objects.filter(
        category_id__in=list(all_cat_ids),
        orderitem__isnull=False
    )

    # Optional date window (e.g., last 30 days)
    if block.days_window:
        since_dt = timezone.now() - timedelta(days=block.days_window)
        # IMPORTANT: Adjust 'order__created_at' to your actual Order model datetime field
        qs = qs.filter(orderitem__order__created_at__gte=since_dt)

    best_sellers = (
        qs
        .annotate(total_sold=Sum("orderitem__quantity"))
        .order_by("-total_sold")
        [: (block.limit or 10)]
    )

    return {
        "best_seller_bicycles": best_sellers,
        "best_seller_block": block,
    }

def home_category_sections(request):
    """
    Multiple homepage sections driven by admin (HomeCategorySection).
    NOW filtered to show ONLY products with is_Featured_Product=True.
    Products are fetched from selected categories + all descendants.
    Ordered by newest first (id desc). Limit 8 per section.
    """
    sections = []
    for sec in HomeCategorySection.objects.all():
        cats = sec.categories.all()
        if not cats.exists():
            sections.append({"title": sec.title, "products": Product.objects.none()})
            continue

        ids = _collect_descendant_ids(cats)
        ids.update(cats.values_list("id", flat=True))

        products = (
            Product.objects
            .filter(category_id__in=list(ids), is_Featured_Product=True, is_available=True)
            .order_by("-id")[:8]
        )
        sections.append({"title": sec.title, "products": products})

    return {"home_category_sections": sections}

def coupon_offers(request):
    offers = CouponCodeOffer.objects.all()
    return {'coupon_offers': offers}