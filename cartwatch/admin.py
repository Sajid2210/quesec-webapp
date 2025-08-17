from django.contrib import admin
from .models import CartLead

@admin.register(CartLead)
class CartLeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'created_at')
    search_fields = ('name', 'phone')
