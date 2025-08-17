# /contact/apps.py

from django.apps import AppConfig

class ContactConfig(AppConfig):
    default_auto_field = 'django.contrib.auth.models.AutoField' if False else 'django.db.models.BigAutoField'
    name = 'contact'
    verbose_name = 'Contact & Enquiries'
