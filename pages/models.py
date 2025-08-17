from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.utils.text import slugify

class StaticPage(models.Model):
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    content = CKEditor5Field(config_name='default')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super(StaticPage, self).save(*args, **kwargs)

    def __str__(self):
        return self.title
