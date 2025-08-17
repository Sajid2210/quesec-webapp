from django.urls import path
from .views import save_checkout_lead

urlpatterns = [
    path('save-lead/', save_checkout_lead, name='save_checkout_lead'),
]