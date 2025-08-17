from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta

# ------------------------------
# Custom User Manager
# ------------------------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        user = self.model(email=self.normalize_email(email))
        user.set_unusable_password()  # since we use OTP login
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.create_user(email)
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)  # needed for admin login
        user.save(using=self._db)
        return user

# ------------------------------
# Custom User Model
# ------------------------------
class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

# ------------------------------
# OTP Model
# ------------------------------
class EmailOTP(models.Model):
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return timezone.now() < self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.user.email}"
