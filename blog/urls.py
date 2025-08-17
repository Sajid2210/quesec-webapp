from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.post_list, name="list"),
    path("category/<slug:category_slug>/", views.category_posts, name="category"),
    # Detail URL requires both: category + post slug
    path("<slug:category_slug>/<slug:slug>/", views.post_detail, name="detail"),
]
