from django.contrib import admin
from .models import StaticPage

@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'created_at', 'updated_at')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title',)
