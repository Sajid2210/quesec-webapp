from django.shortcuts import render, get_object_or_404
from .models import StaticPage

def static_page_detail(request, slug):
    page = get_object_or_404(StaticPage, slug=slug)
    return render(request, 'pages/static_page_detail.html', {'page': page})
