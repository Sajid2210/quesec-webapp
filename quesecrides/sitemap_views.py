# /quesecrides/sitemap_views.py

from django.http import HttpResponse
from django.urls import reverse
from django.utils.timezone import now
from django.db.models import Max
from datetime import timedelta

# ---- Import your models ----
from bicycles.models import Category, Product

# Blog models optional (safe import)
try:
    from blog.models import BlogCategory, BlogPost
except Exception:
    BlogCategory = None
    BlogPost = None

# ===========================
# CONFIG: Priorities & Changefreq
# ===========================
SITEMAP_RULES = {
    # Core
    "home":            {"changefreq": "daily",   "priority": "1.0"},
    "shop":            {"changefreq": "daily",   "priority": "0.90"},
    "cat_parent":      {"changefreq": "daily",   "priority": "0.85"},
    "cat_child":       {"changefreq": "daily",   "priority": "0.80"},
    # Products (fresh = updated in last 14 days)
    "product_fresh":   {"changefreq": "daily",   "priority": "0.80"},
    "product_stale":   {"changefreq": "weekly",  "priority": "0.65"},
    # Blog
    "blog_list":       {"changefreq": "weekly",  "priority": "0.60"},
    "blog_category":   {"changefreq": "weekly",  "priority": "0.55"},
    # Blog post (fresh = updated in last 30 days)
    "blog_fresh":      {"changefreq": "weekly",  "priority": "0.60"},
    "blog_stale":      {"changefreq": "monthly", "priority": "0.50"},
}

PRODUCT_FRESH_DAYS = 14
BLOG_FRESH_DAYS = 30
PRODUCT_PAGE_SIZE = 5000  # Google guideline-friendly splitting

# ===========================
# Helpers
# ===========================
def _abs(request, path: str) -> str:
    base = request.build_absolute_uri('/')[:-1]
    return f"{base}{path}"

def _xml_header() -> list[str]:
    return ['<?xml version="1.0" encoding="UTF-8"?>']

def _fmt_date(dt) -> str:
    try:
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return now().strftime("%Y-%m-%d")

def _is_fresh(dt, days: int) -> bool:
    if not dt:
        return False
    return (now() - dt) <= timedelta(days=days)

def _category_lastmod(cat: Category):
    """
    Category ke lastmod ko us category + uske child categories ke products
    ke max(updated_at) se nikaalo. Agar kuch nahi mile to 'now()'.
    """
    try:
        cats = [cat] + list(cat.children.all())
        last = (Product.objects.filter(category__in=cats)
                .aggregate(last=Max('updated_at'))['last'])
        return last or now()
    except Exception:
        return now()

# ===========================
# robots.txt
# ===========================
def robots_txt(request):
    lines = [
        "User-agent: *",
        # ⚠ Admin path intentionally not listed for security-by-obscurity
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /login/",
        "Disallow: /logout/"
        "Disallow: /verify-otp/",
        "Disallow: /my-account/",
        "Disallow: /page/",
        "Disallow: /search/",
        "Disallow: /coupons/",
        "Disallow: /contact/",
        "Disallow: /ckeditor5/",
        f"Sitemap: {_abs(request, reverse('sitemap_index'))}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

# ===========================
# sitemap index → child sitemaps
# ===========================
def sitemap_index(request):
    rows = _xml_header()
    rows.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    rows.append("  <sitemap>")
    rows.append(f"    <loc>{_abs(request, reverse('sitemap_static'))}</loc>")
    rows.append(f"    <lastmod>{_fmt_date(now())}</lastmod>")
    rows.append("  </sitemap>")

    rows.append("  <sitemap>")
    rows.append(f"    <loc>{_abs(request, reverse('sitemap_categories'))}</loc>")
    rows.append(f"    <lastmod>{_fmt_date(now())}</lastmod>")
    rows.append("  </sitemap>")

    total = Product.objects.count()
    pages = max(1, (total + PRODUCT_PAGE_SIZE - 1) // PRODUCT_PAGE_SIZE)
    for p in range(1, pages + 1):
        rows.append("  <sitemap>")
        rows.append(f"    <loc>{_abs(request, reverse('sitemap_products', args=[p]))}</loc>")
        rows.append(f"    <lastmod>{_fmt_date(now())}</lastmod>")
        rows.append("  </sitemap>")

    rows.append("  <sitemap>")
    rows.append(f"    <loc>{_abs(request, reverse('sitemap_blog'))}</loc>")
    rows.append(f"    <lastmod>{_fmt_date(now())}</lastmod>")
    rows.append("  </sitemap>")

    rows.append("</sitemapindex>")
    return HttpResponse("\n".join(rows), content_type="application/xml")

# ===========================
# Static (Home + Shop)
# ===========================
def sitemap_static(request):
    rows = _xml_header()
    rows.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # Home
    rows.append("  <url>")
    rows.append(f"    <loc>{_abs(request, reverse('home'))}</loc>")
    rows.append(f"    <lastmod>{_fmt_date(now())}</lastmod>")
    rows.append(f"    <changefreq>{SITEMAP_RULES['home']['changefreq']}</changefreq>")
    rows.append(f"    <priority>{SITEMAP_RULES['home']['priority']}</priority>")
    rows.append("  </url>")

    # Shop
    try:
        rows.append("  <url>")
        rows.append(f"    <loc>{_abs(request, reverse('shop-page'))}</loc>")
        rows.append(f"    <lastmod>{_fmt_date(now())}</lastmod>")
        rows.append(f"    <changefreq>{SITEMAP_RULES['shop']['changefreq']}</changefreq>")
        rows.append(f"    <priority>{SITEMAP_RULES['shop']['priority']}</priority>")
        rows.append("  </url>")
    except Exception:
        pass

    rows.append("</urlset>")
    return HttpResponse("\n".join(rows), content_type="application/xml")

# ===========================
# Categories (parent + child)
# ===========================
def sitemap_categories(request):
    rows = _xml_header()
    rows.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    parents = Category.objects.filter(parent__isnull=True).prefetch_related('children')
    for p in parents:
        # Parent
        try:
            url = _abs(request, reverse('category-parent', args=[p.slug]))
            last = _category_lastmod(p)
            rows.append("  <url>")
            rows.append(f"    <loc>{url}</loc>")
            rows.append(f"    <lastmod>{_fmt_date(last)}</lastmod>")
            rows.append(f"    <changefreq>{SITEMAP_RULES['cat_parent']['changefreq']}</changefreq>")
            rows.append(f"    <priority>{SITEMAP_RULES['cat_parent']['priority']}</priority>")
            rows.append("  </url>")
        except Exception:
            pass

        # Children
        for c in getattr(p, 'children', []).all():
            try:
                url = _abs(request, reverse('category-child', args=[p.slug, c.slug]))
                last = _category_lastmod(c)
                rows.append("  <url>")
                rows.append(f"    <loc>{url}</loc>")
                rows.append(f"    <lastmod>{_fmt_date(last)}</lastmod>")
                rows.append(f"    <changefreq>{SITEMAP_RULES['cat_child']['changefreq']}</changefreq>")
                rows.append(f"    <priority>{SITEMAP_RULES['cat_child']['priority']}</priority>")
                rows.append("  </url>")
            except Exception:
                pass

    rows.append("</urlset>")
    return HttpResponse("\n".join(rows), content_type="application/xml")

# ===========================
# Products (paginated) + dynamic fresh/stale + images (main + gallery)
# ===========================
def sitemap_products(request, page=1):
    start = (int(page) - 1) * PRODUCT_PAGE_SIZE
    end = start + PRODUCT_PAGE_SIZE
    qs = Product.objects.select_related('category', 'category__parent').order_by('id')[start:end]

    rows = _xml_header()
    rows.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">')

    for prod in qs:
        cat = getattr(prod, 'category', None)
        if not cat:
            continue
        parent = getattr(cat, 'parent', None)

        # Destination URL
        try:
            if parent:
                loc = _abs(request, reverse('product-detail-child', args=[parent.slug, cat.slug, prod.slug]))
            else:
                loc = _abs(request, reverse('product-detail', args=[cat.slug, prod.slug]))
        except Exception:
            continue

        # Freshness
        last = getattr(prod, 'updated_at', None) or getattr(prod, 'created_at', None) or now()
        fresh = _is_fresh(last, PRODUCT_FRESH_DAYS)
        rule_key = 'product_fresh' if fresh else 'product_stale'

        rows.append("  <url>")
        rows.append(f"    <loc>{loc}</loc>")
        rows.append(f"    <lastmod>{_fmt_date(last)}</lastmod>")
        rows.append(f"    <changefreq>{SITEMAP_RULES[rule_key]['changefreq']}</changefreq>")
        rows.append(f"    <priority>{SITEMAP_RULES[rule_key]['priority']}</priority>")

        # ---- Images: main + gallery ----
        # Main image: Product.image
        try:
            if getattr(prod, 'image', None) and getattr(prod.image, 'url', None):
                rows.append("    <image:image>")
                rows.append(f"      <image:loc>{_abs(request, prod.image.url)}</image:loc>")
                rows.append("    </image:image>")
        except Exception:
            pass

        # Gallery images: Product.gallery (related_name)
        try:
            gallery = getattr(prod, 'gallery', None)
            if gallery is not None:
                for gi in gallery.all():
                    if getattr(gi, 'image', None) and getattr(gi.image, 'url', None):
                        rows.append("    <image:image>")
                        rows.append(f"      <image:loc>{_abs(request, gi.image.url)}</image:loc>")
                        rows.append("    </image:image>")
        except Exception:
            pass

        rows.append("  </url>")

    rows.append("</urlset>")
    return HttpResponse("\n".join(rows), content_type="application/xml")

# ===========================
# Blog (list + category + detail) + dynamic fresh/stale
# ===========================
def sitemap_blog(request):
    rows = _xml_header()
    rows.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # Agar blog app hi nahi hai, to empty sitemap return kar do
    if BlogCategory is None or BlogPost is None:
        rows.append("</urlset>")
        return HttpResponse("\n".join(rows), content_type="application/xml")

    # Blog list page
    try:
        rows.append("  <url>")
        rows.append(f"    <loc>{_abs(request, reverse('blog:list'))}</loc>")
        rows.append(f"    <lastmod>{_fmt_date(now())}</lastmod>")
        rows.append(f"    <changefreq>{SITEMAP_RULES['blog_list']['changefreq']}</changefreq>")
        rows.append(f"    <priority>{SITEMAP_RULES['blog_list']['priority']}</priority>")
        rows.append("  </url>")
    except Exception:
        pass

    # Blog category pages
    for bcat in BlogCategory.objects.all():
        try:
            # Prefer model's get_absolute_url if available
            try:
                cat_url = _abs(request, bcat.get_absolute_url())
            except Exception:
                # fallback to reverse('blog:category', args=[slug])
                cat_url = _abs(request, reverse('blog:category', args=[bcat.slug]))

            last = (BlogPost.objects.filter(status='published', category=bcat)
                    .aggregate(last=Max('updated_at'))['last']) or now()
            rows.append("  <url>")
            rows.append(f"    <loc>{cat_url}</loc>")
            rows.append(f"    <lastmod>{_fmt_date(last)}</lastmod>")
            rows.append(f"    <changefreq>{SITEMAP_RULES['blog_category']['changefreq']}</changefreq>")
            rows.append(f"    <priority>{SITEMAP_RULES['blog_category']['priority']}</priority>")
            rows.append("  </url>")
        except Exception:
            pass

    # Blog posts (published only)
    posts = BlogPost.objects.filter(status='published').select_related('category')
    for p in posts:
        try:
            try:
                loc = _abs(request, p.get_absolute_url())
            except Exception:
                # fallback: /blog/<category_slug>/<post_slug> expected
                loc = _abs(request, reverse('blog:detail', args=[p.category.slug, p.slug]))

            stamp = p.updated_at or getattr(p, 'published_at', None) or now()
            fresh = _is_fresh(stamp, BLOG_FRESH_DAYS)
            rule_key = 'blog_fresh' if fresh else 'blog_stale'

            rows.append("  <url>")
            rows.append(f"    <loc>{loc}</loc>")
            rows.append(f"    <lastmod>{_fmt_date(stamp)}</lastmod>")
            rows.append(f"    <changefreq>{SITEMAP_RULES[rule_key]['changefreq']}</changefreq>")
            rows.append(f"    <priority>{SITEMAP_RULES[rule_key]['priority']}</priority>")
            rows.append("  </url>")
        except Exception:
            pass

    rows.append("</urlset>")
    return HttpResponse("\n".join(rows), content_type="application/xml")
