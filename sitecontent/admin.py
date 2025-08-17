from django.contrib import admin
from .models import SiteSettings, NavMenu, FtNavMenu2, FtNavMenu3, CatMenu, FtNavMenu1, Hero, HeroTwo, CouponCodeOffer, BestSellerBlock, HomeCategorySection
from .forms import CatMenuForm, NavMenuForm

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Agar SiteSettings already ek bar exist karta hai to add form disable ho jayega
        if SiteSettings.objects.exists():
            return False
        return True
    
class CatMenuAdmin(admin.ModelAdmin):
    form = CatMenuForm
    list_display = ['name', 'parent', 'is_parent']
    list_filter = ['is_parent', 'parent']
    search_fields = ['name']

class NavMenuAdmin(admin.ModelAdmin):
    form = NavMenuForm
    list_display = ['name', 'parent', 'is_parent']
    list_filter = ['is_parent', 'parent']
    search_fields = ['name']


@admin.register(Hero)
class HeroAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Sirf ek record allow karo
        if Hero.objects.exists():
            return False
        return True

@admin.register(HeroTwo)
class HeroTwoAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Sirf ek record allow karo
        if HeroTwo.objects.exists():
            return False
        return True
    
@admin.register(BestSellerBlock)
class BestSellerBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "limit", "days_window")
    search_fields = ("title",)
    filter_horizontal = ("categories",)
    def has_add_permission(self, request):
        # Allow adding only if no instance exists
        if BestSellerBlock.objects.exists():
            return False
        return True
    
@admin.register(HomeCategorySection)
class HomeCategorySectionAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)
    filter_horizontal = ("categories",)
    
admin.site.register(NavMenu, NavMenuAdmin)
admin.site.register(FtNavMenu1)
admin.site.register(FtNavMenu2)
admin.site.register(FtNavMenu3)
admin.site.register(CouponCodeOffer)
admin.site.register(CatMenu, CatMenuAdmin)
