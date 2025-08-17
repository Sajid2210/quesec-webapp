from django.db import models
from django.conf import settings
from bicycles.models import Product

class Order(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    pincode = models.CharField(max_length=6)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    company = models.CharField(max_length=100, blank=True, null=True)
    gst = models.CharField(max_length=20, blank=True, null=True)
    payment_status = models.CharField(max_length=20, default="Pending")
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    payment_method = models.CharField(max_length=20, choices=(
        ('full', 'Razorpay Full'),
        ('cod', 'COD with 20% Advance'),
        ('payu', 'PayU Full'),
        ('payu_upi', 'PayU UPI'),
    ))

    total_amount = models.FloatField()
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon_discount = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.title} (x{self.quantity})"