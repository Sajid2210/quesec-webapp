from django.contrib import admin
from .models import Product, Category, ProductImage, ProductSpecification, Specification, ProductReview, ProductQuestion, ProductAnswer
from import_export import resources, fields
from django.db.models import BooleanField
from django.urls import path
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from import_export.widgets import BooleanWidget
from django import forms
from import_export.admin import ImportExportModelAdmin
from django.forms.models import BaseInlineFormSet


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

    class Media:
        js = ('admin/js/category_toggle.js',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    form = CategoryForm
    list_display = ['name', 'parent', 'is_parent']
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ['parent', 'is_parent']


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        import_id_fields = ['slug']
        exclude = ('created_at', 'updated_at')
                
class ProductImageInline(admin.StackedInline):
    model = ProductImage
    extra = 4

class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "specification":
            kwargs["queryset"] = Specification.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'value']

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'

    

@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ['question']


class ProductAnswerInline(admin.TabularInline):
    model = ProductAnswer
    extra = 1

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    form = ProductForm
    resource_class = ProductResource
    list_display = ['title', 'price', 'discount_price', 'is_available', 'category', 'duplicate_button']
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ProductImageInline, ProductSpecificationInline, ProductAnswerInline]
    change_form_template = "admin/bicycles/product/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:product_id>/duplicate/', self.admin_site.admin_view(self.duplicate_product), name='duplicate-product'),
        ]
        return custom_urls + urls

    def duplicate_button(self, obj):
        return format_html(
            '<a class="button" style="background-color:#198754; padding:4px 10px; color:white; border-radius:4px; text-decoration:none;" href="{}">Duplicate</a>',
            f'{obj.id}/duplicate/'
        )
    duplicate_button.short_description = 'Duplicate Product'
    duplicate_button.allow_tags = True

    def duplicate_product(self, request, product_id):
        try:
            original = Product.objects.get(pk=product_id)
            copy = Product.objects.get(pk=product_id)
            copy.pk = None
            copy.title = f"{original.title} - duplicate"  # Leave blank
            copy.slug = f"{original.slug}-duplicate"   # Leave blank
            copy.image = None   # blank main image
            copy.save()

            self.message_user(request, "Product duplicated successfully!", messages.SUCCESS)
            return redirect(f'../../{copy.id}/change/')
        except Product.DoesNotExist:
            self.message_user(request, "Product not found", messages.ERROR)
            return redirect("../")


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at']
