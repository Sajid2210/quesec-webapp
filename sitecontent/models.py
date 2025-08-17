from django.db import models
from django.utils.text import slugify

class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100)
    site_description = models.CharField(max_length=100)
    site_keywords = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='logos/')
    favicon = models.ImageField(upload_to='logos/', blank=True)
    address = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    instagram_link = models.URLField()
    facebook_link = models.URLField()
    x_link = models.URLField()
    youtube_link = models.URLField()
    footer_text = models.TextField(blank=True)

    def __str__(self):
        return self.site_name

class NavMenu(models.Model):
    name = models.CharField(max_length=50)
    link = models.URLField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    is_parent = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class CatMenu(models.Model):
    name = models.CharField(max_length=50)
    link = models.URLField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    is_parent = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class FtNavMenu1(models.Model):
    name = models.CharField(max_length=50)
    link = models.URLField()

    def __str__(self):
        return self.name
    

class FtNavMenu2(models.Model):
    name = models.CharField(max_length=50)
    link = models.URLField()

    def __str__(self):
        return self.name
    
class FtNavMenu3(models.Model):
    name = models.CharField(max_length=50)
    link = models.URLField()

    def __str__(self):
        return self.name
    
class Hero(models.Model):
    image = models.ImageField(
        upload_to='hero/',
        help_text='Recommended image size: 1150 × 670 px'
    )
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"Hero Image {self.id}"

class HeroTwo(models.Model):
    image = models.ImageField(
        upload_to='hero2/',
        help_text='Recommended image size: 415 × 670 px'
    )
    link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"HeroTwo Image {self.id}"
    

class CouponCodeOffer(models.Model):
    image_left = models.ImageField(upload_to='offers/', help_text="Recommended image size: 290 × 90 px")
    image_right = models.FileField(upload_to='offers/', help_text="Add SVG image")

    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200)
    validity = models.CharField(max_length=100)
    coupon_code = models.CharField(max_length=50)

    COLOR_CHOICES = [
        ('Red', 'Red'),
        ('Blue', 'Blue'),
        ('Orange', 'Orange'),
    ]
    color = models.CharField(max_length=10, choices=COLOR_CHOICES, default='Blue')

    def __str__(self):
        return f"{self.title} - {self.coupon_code}"
    
class BestSellerBlock(models.Model):
    """
    Admin-configurable best seller section.
    - Select multiple categories (parent/child allowed)
    - We include ALL descendants of those categories on the homepage
    - Optional time window to compute best sellers (last N days)
    """
    title = models.CharField(max_length=120, default="Best Seller Bicycles")
    categories = models.ManyToManyField(
        'bicycles.Category',
        blank=True,
        related_name='best_seller_blocks',
        help_text="Select one or more root categories (child categories auto-include)."
    )
    limit = models.PositiveIntegerField(default=10, help_text="How many products to show")
    days_window = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Limit to last N days of sales (leave empty for all-time)"
    )

    class Meta:
        verbose_name = "Best Seller Block"
        verbose_name_plural = "Best Seller Blocks"

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and BestSellerBlock.objects.exists():
            raise ValueError("Only one BestSellerBlock instance is allowed. Please edit the existing one.")
        super().save(*args, **kwargs)

class HomeCategorySection(models.Model):
    title = models.CharField(max_length=120)
    categories = models.ManyToManyField(
        'bicycles.Category',
        blank=True,
        related_name='home_sections',
        help_text="Select categories for this section (all descendants auto-included)."
    )

    class Meta:
        verbose_name = "Home Category Section"
        verbose_name_plural = "Home Category Sections"

    def __str__(self):
        return self.title