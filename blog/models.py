from django.db import models
from django.utils.text import slugify
from django.urls import reverse

class BlogCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, help_text="URL path for this category")

    class Meta:
        verbose_name_plural = "Blog Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        # /blog/category/<slug>/
        return reverse('blog:category', args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


STATUS_CHOICES = (
    ("draft", "Draft"),
    ("published", "Published"),
)

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, help_text="URL path for this post")
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, related_name="posts")
    author_name = models.CharField(max_length=120)
    excerpt = models.TextField(blank=True)
    content = models.TextField()
    cover_image = models.ImageField(upload_to="blog/", blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """
        Detail URL ab 2 slugs use karta hai:
        /blog/<category_slug>/<slug>/
        """
        return reverse('blog:detail', args=[self.category.slug, self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
