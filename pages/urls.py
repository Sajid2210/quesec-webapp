from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/', views.static_page_detail, name='static_page_detail'),
]
