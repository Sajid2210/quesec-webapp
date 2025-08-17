from django.db import models

class CartLead(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    cart_items = models.TextField()  # Store product info as text/JSON
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone})"
