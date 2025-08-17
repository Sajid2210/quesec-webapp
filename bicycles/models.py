from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.core.validators import RegexValidator
from django.db.models import UniqueConstraint
from django.conf import settings



class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    meta_description = models.TextField(blank=True, max_length=160, null=True)
    image = models.ImageField(
        upload_to='category_images/',
        null=True,
        blank=True,
        help_text='Recommended image size: 130 × 130 px clear backgound image'
    )
    
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_parent = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.parent:
            return f"/{self.parent.slug}/{self.slug}/"
        else:
            return f"/{self.slug}/"

    @property
    def total_products(self):
        # Import lazily to avoid circular import
        from .models import Product

        # Collect all child categories including self
        categories = [self]
        categories += list(self.children.all())

        return Product.objects.filter(category__in=categories).count()


class Specification(models.Model):
    title = models.CharField(max_length=100)
    value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.title} – {self.value}"


class ProductSpecification(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='product_specifications')
    specification = models.ForeignKey(Specification, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.title} ⟶ {self.specification.title}"

    class Meta:
        constraints = [
            UniqueConstraint(fields=['product', 'specification'], name='unique_product_spec')
        ]

class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    sku = models.CharField(unique=True, max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    short_desc = CKEditor5Field('Short Notes', config_name='basic')
    description = CKEditor5Field('Description', config_name='default')
    color_1_name = models.CharField(max_length=30, blank=True, help_text="Color name (e.g. Red)")
    color_1_code = models.CharField(
        max_length=7,
        blank=True,
        validators=[RegexValidator(regex='^#(?:[0-9a-fA-F]{3}){1,2}$')],
        help_text="Hex code (e.g. #FF0000)"
    )

    color_2_name = models.CharField(max_length=30, blank=True, help_text="Optional second color name")
    color_2_code = models.CharField(
        max_length=7,
        blank=True,
        validators=[RegexValidator(regex='^#(?:[0-9a-fA-F]{3}){1,2}$')],
        help_text="Optional second color hex code"
    )
    age_group = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    weight = models.PositiveIntegerField(default=0)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Shipping cost for this product")
    is_available = models.BooleanField(default=True)
    is_Featured_Product = models.BooleanField(default=True)
    is_bicycle = models.BooleanField(default=False)
    is_dirtbike = models.BooleanField(default=False)
    is_ATVs = models.BooleanField(default=False)
    is_Accessories = models.BooleanField(default=False)
    amazon_link = models.URLField(max_length=200, blank=True, null=True)
    meta_title = models.CharField(max_length=60, blank=True, null=True)
    meta_description = models.TextField(max_length=160, blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.sku
    
    def get_absolute_url(self):
        if self.category.parent:
            return f'/{self.category.parent.slug}/{self.category.slug}/{self.slug}/'
        else:
            return f'/{self.category.slug}/{self.slug}/'
        
    def display_category(self):
        # Agar parent hai to matlab yeh child category hai → sirf current category ka naam do
        return self.category.name
    
    @property
    def discount_percentage(self):
        if self.discount_price and self.price:
            try:
                discount = ((self.price - self.discount_price) / self.price) * 100
                return round(discount)
            except ZeroDivisionError:
                return 0
        return 0
    
    @property
    def discount_amount(self):
        if self.discount_price and self.price:
            try:
                discount = self.price - self.discount_price
                return round(discount)
            except ZeroDivisionError:
                return 0
        return 0
    @property
    def stock_percentage(self):
        try:
            return min(round((self.stock / 100) * 100), 100)
        except:
            return 0
    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg']
            return round(avg, 2)
        return 0
        
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='product-gallery/')

    def __str__(self):
        return f"{self.product.title} Image"
    
class ProductReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.TextField(max_length=100)
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} Stars") for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'product')  # ✅ user ek baar hi review de

    def __str__(self):
        return f"{self.user.email} on {self.product.title} – {self.rating}★"
    
class ProductQuestion(models.Model):
    question = models.CharField(max_length=255)

    def __str__(self):
        return self.question


class ProductAnswer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_qas')
    question = models.ForeignKey(ProductQuestion, on_delete=models.CASCADE)
    answer = models.TextField()

    def __str__(self):
        return f"{self.product.title} ⟶ {self.question.question}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['product', 'question'], name='unique_product_question')
        ]