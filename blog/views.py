from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from .models import BlogPost, BlogCategory

def post_list(request):
    posts_qs = BlogPost.objects.filter(status="published").select_related("category")
    paginator = Paginator(posts_qs, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = BlogCategory.objects.all()
    context = {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": None,
    }
    return render(request, "blog/list.html", context)

def post_detail(request, category_slug, slug):
    """
    URL me category_slug aata hai, lekin lookup ke liye zaroori nahi.
    Phir bhi consistency ke liye category bhi check kar rahe hain.
    """
    post = get_object_or_404(
        BlogPost, slug=slug, status="published", category__slug=category_slug
    )
    related = BlogPost.objects.filter(
        status="published", category=post.category
    ).exclude(id=post.id)[:4]

    context = {
        "post": post,
        "related": related,
    }
    return render(request, "blog/detail.html", context)

def category_posts(request, category_slug):
    category = get_object_or_404(BlogCategory, slug=category_slug)
    posts_qs = BlogPost.objects.filter(status="published", category=category).select_related("category")
    paginator = Paginator(posts_qs, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    categories = BlogCategory.objects.all()
    context = {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": category.slug,
    }
    return render(request, "blog/list.html", context)
