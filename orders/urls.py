from django.urls import path
from . import views

urlpatterns = [
    path('save-order/', views.save_order, name='save_order'),
    path("payu-initiate/", views.payu_initiate, name="payu-initiate"),
    path('payu-initiate-upi/', views.payu_initiate_upi, name='payu-initiate-upi'),
    path("payu-success/", views.payu_success, name="payu-success"),
    path("payu-failure/", views.payu_failure, name="payu-failure"),
    path('thank-you/', views.thank_you, name='thank_you'),
]
