from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from bicycles.models import Product, Category

def search_view(request):
    """
    /search/?q=...  -> HTML results page (paginated)
    Matches: title, description, short_desc, SKU, category name/slug.
    """
    query = (request.GET.get("q") or "").strip()
    page_no = int(request.GET.get("page") or 1)

    products = Product.objects.none()
    total = 0

    if query:
        # Jo category query ko match karti ho (name ya slug)
        cat_ids = list(
            Category.objects.filter(
                Q(name__icontains=query) | Q(slug__icontains=query)
            ).values_list("id", flat=True)
        )

        # ✅ Yaha correct field names use kiye gaye hain:
        # - short_desc  (NOT short_description)
        # - description (NOT long_description)
        products = (
            Product.objects.select_related("category")
            .filter(is_available=True)
            .filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(short_desc__icontains=query) |
                Q(sku__icontains=query) |
                Q(category_id__in=cat_ids)
            )
            .order_by("-id")
        )

        total = products.count()

    paginator = Paginator(products, 24)  # 24 items per page
    page_obj = paginator.get_page(page_no)

    ctx = {
        "query": query,
        "total": total,
        "page_obj": page_obj,
        "products": page_obj.object_list,
    }
    return render(request, "search_results.html", ctx)


from django.http import JsonResponse

def search_suggest(request):
    """
    /search/suggest/?q=... -> JSON suggestions for live dropdown
    Fields: title / sku (correct), price, url, image
    """
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse({"items": []})

    qs = (
        Product.objects.filter(is_available=True)
        .filter(Q(title__icontains=q) | Q(sku__icontains=q))
        .order_by("-id")[:8]
    )

    items = []
    for p in qs:
        try:
            url = p.get_absolute_url()
        except Exception:
            url = "#"

        items.append({
            "title": p.title,
            "sku": getattr(p, "sku", ""),
            "price": float(p.discount_price) if getattr(p, "discount_price", None) else 0.0,
            "url": url,
            "image": p.image.url if getattr(p, "image", None) else "",
        })

    return JsonResponse({"items": items})
