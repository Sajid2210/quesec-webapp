from django.urls import path
from .views import shop_view, product_detail_view, category_view

urlpatterns = [
    path('shop/', shop_view, name='shop-page'), 
    # Category Page URLs
    path('<slug:parent_slug>/<slug:child_slug>/', category_view, name='category-child'),
    path('<slug:parent_slug>/', category_view, name='category-parent'),

    # Product Detail URLs (Child & Direct)
    path('<slug:category_slug>/<slug:product_slug>/', product_detail_view, name='product-detail'),
    path('<slug:parent_slug>/<slug:child_slug>/<slug:product_slug>/', product_detail_view, name='product-detail-child'),
]