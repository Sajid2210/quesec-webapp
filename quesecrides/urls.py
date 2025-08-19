"""
URL configuration for quesecrides project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings
from django.http import HttpResponse
from quesecrides import views
from quesecrides.search_views import search_view, search_suggest

from .sitemap_views import (
    robots_txt, sitemap_index, sitemap_static, sitemap_categories,
    sitemap_products, sitemap_blog
)

urlpatterns = [
    path("safiya/", admin.site.urls),

    # Health check (diagnostic)
    path("healthz/", lambda r: HttpResponse("ok"), name="healthz"),

    # Home
    path("", views.home, name="home"),

    # Cart / Checkout
    path("add-to-cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("cart/", views.view_cart, name="view_cart"),
    path("update-qty/", views.update_qty, name="update_qty"),
    path("remove-from-cart/<int:product_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/checkout/", views.checkout_page, name="checkout_page"),

    # Apps include
    path("cartwatch/", include("cartwatch.urls")),
    path("search/", search_view, name="search"),
    path("search/suggest/", search_suggest, name="search_suggest"),
    path("blog/", include("blog.urls", namespace="blog")),
    path("page/", include("pages.urls")),
    path("contact/", include("contact.urls")),
    path("", include("coupons.urls")),
    path("", include("orders.urls")),
    path("", include("accounts.urls")),
    path("", include("bicycles.urls")),

    # CKEditor
    path("ckeditor5/", include("django_ckeditor_5.urls")),

    # Robots & Sitemaps
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap_index, name="sitemap_index"),
    path("sitemap-static.xml", sitemap_static, name="sitemap_static"),
    path("sitemap-categories.xml", sitemap_categories, name="sitemap_categories"),
    path("sitemap-products-<int:page>.xml", sitemap_products, name="sitemap_products"),
    path("sitemap-blog.xml", sitemap_blog, name="sitemap_blog"),
]

# DEBUG=False me local static/media serve (dev-only)
if not settings.DEBUG:
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]

# Custom error handlers
handler404 = "quesecrides.views.custom_page_not_found"
handler500 = "quesecrides.views.custom_server_error"
