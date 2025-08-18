"""
Django settings for quesecrides project.
"""
from pathlib import Path
import os
import mimetypes
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Core ──────────────────────────────────────────────────────────────────────
DEBUG = config("DEBUG", cast=bool, default=False)
# Accept comma-separated hosts from env
_host_csv = config("ALLOWED_HOSTS", default="127.0.0.1,localhost")
ALLOWED_HOSTS = [h.strip() for h in _host_csv.split(",") if h.strip()]
SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me")

# ── Apps ──────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "import_export",
    "coupons",
    "django_ckeditor_5",
    "sitecontent",
    "bicycles",
    "cartwatch",
    "accounts",
    "orders",
    "blog",
    "pages",
    "contact",
    # S3 storage
    "storages",
]

# ── Middleware (WhiteNoise just after Security) ───────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "quesecrides.middleware.seo_index_middleware.SEOIndexControlMiddleware",
]

ROOT_URLCONF = "quesecrides.urls"

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "sitecontent.context_processors.site_info",
                "sitecontent.context_processors.shop_categories",
                "sitecontent.context_processors.best_seller_bicycles",
                "sitecontent.context_processors.coupon_offers",
                "sitecontent.context_processors.home_category_sections",
            ],
        },
    },
]

WSGI_APPLICATION = "quesecrides.wsgi.application"

# ── Database ──────────────────────────────────────────────────────────────────
# If DB_ENGINE provided, use Postgres; else fall back to SQLite
DB_ENGINE = config("DB_ENGINE", default="")
if DB_ENGINE:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": config("DB_NAME"),
            "USER": config("DB_USER"),
            "PASSWORD": config("DB_PASSWORD"),
            "HOST": config("DB_HOST"),
            "PORT": config("DB_PORT", default="5432"),
            # Optional SSL (enable on production once certs are sorted)
            # "OPTIONS": {"sslmode": "require"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ── Password validators ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── I18N ──────────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_L10N = True
USE_TZ = False

# ── Static ────────────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"  
STATICFILES_DIRS = []

# Django 5: STORAGES must define 'staticfiles'; 'default' depends on S3 flag
USE_S3_MEDIA = bool(config("AWS_STORAGE_BUCKET_NAME", default=""))
if USE_S3_MEDIA:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

# ── Media ─────────────────────────────────────────────────────────────────────
if USE_S3_MEDIA:
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID", default="")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY", default="")
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME", default="")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="ap-south-1")
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    _s3_domain = config(
        "AWS_S3_CUSTOM_DOMAIN",
        default=f"{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com" if AWS_STORAGE_BUCKET_NAME else "",
    )
    MEDIA_URL = f"https://{_s3_domain}/"
    MEDIA_ROOT = ""  # not used on disk
else:
    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ── Custom user ───────────────────────────────────────────────────────────────
AUTH_USER_MODEL = "accounts.CustomUser"

# ── CKEditor ──────────────────────────────────────────────────────────────────
CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading","|","bold","italic","link","underline","|",
            "numberedList","bulletedList","|","blockQuote","codeBlock","|",
            "undo","redo"
        ],
        "height": "300px","width": "100%","language": "en",
    },
    "basic": {"toolbar": ["bulletedList"], "height": "100px", "width": "100%", "language": "en"},
}

# Allow SVG
mimetypes.add_type("image/svg+xml", ".svg", True)

# ── Email (from .env) ─────────────────────────────────────────────────────────
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="localhost")
EMAIL_PORT = config("EMAIL_PORT", cast=int, default=25)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool, default=False)
EMAIL_TIMEOUT = config("EMAIL_TIMEOUT", cast=int, default=30)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default=(EMAIL_HOST_USER or "webmaster@localhost"))

# ── Payments (from .env) ──────────────────────────────────────────────────────
PAYU_MERCHANT_KEY = config("PAYU_MERCHANT_KEY", default="")
PAYU_MERCHANT_SALT = config("PAYU_MERCHANT_SALT", default="")
PAYU_BASE_URL = config("PAYU_BASE_URL", default="https://test.payu.in")
RAZORPAY_KEY = config("RAZORPAY_KEY", default="")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Diagnostics ───────────────────────────────────────────────────────────────
DEBUG_PROPAGATE_EXCEPTIONS = True
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "ERROR", "propagate": True},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": True},
    },
}
