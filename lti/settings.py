# settings.py

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
load_dotenv(BASE_DIR / ".env")

# ----------------------------------------------------
# SECURITY
# ----------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-default-key-change-me")
DEBUG = os.getenv("DEBUG", "false").strip().lower() in ["1", "true", "yes", "on"]

raw_hosts = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "").split(",") if h.strip()]
render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_host:
    raw_hosts.append(render_host)
if DEBUG:
    raw_hosts += ["127.0.0.1", "localhost"]
ALLOWED_HOSTS = list(dict.fromkeys(raw_hosts))

# ----------------------------------------------------
# Application / Django
# ----------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tool',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'lti.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lti.wsgi.application'

# ----------------------------------------------------
# DATABASE
# ----------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        'NAME': os.getenv("DB_NAME", BASE_DIR / 'db.sqlite3'),
        'USER': os.getenv("DB_USER", ""),
        'PASSWORD': os.getenv("DB_PASSWORD", ""),
        'HOST': os.getenv("DB_HOST", ""),
        'PORT': os.getenv("DB_PORT", ""),
    }
}
database_url = os.getenv("DATABASE_URL", "").strip()
if database_url:
    DATABASES["default"] = dj_database_url.parse(
        database_url,
        conn_max_age=600,
        ssl_require=not DEBUG,
    )

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {"NAME": 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {"NAME": 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {"NAME": 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-uk'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = "/app/login/"
LOGIN_REDIRECT_URL = "/app/"


# ----------------------------------------------------
# COOKIES / SECURITY for LTI
# ----------------------------------------------------

SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_DOMAIN = None  # Must be None for cross-site LTI

CSRF_COOKIE_SAMESITE = None
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
if render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").strip().lower() in ["1", "true", "yes", "on"] and not DEBUG
USE_X_FORWARDED_HOST = True

SESSION_ENGINE = "django.contrib.sessions.backends.db"
X_FRAME_OPTIONS = "ALLOWALL"

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "tool" / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ----------------------------------------------------
# MEDIA (File uploads)
# ----------------------------------------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("MEDIA_ROOT", BASE_DIR / "media"))

# ----------------------------------------------------
# Email (default to console for dev)
# ----------------------------------------------------
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@machinaviva.local")
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "25"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "false").strip().lower() in ["1", "true", "yes", "on"]


# ----------------------------------------------------
# LTI Platform configuration (used for default ToolConfig)
# ----------------------------------------------------
LTI_ISS = os.getenv("LTI_ISS", "")
LTI_CLIENT_ID = os.getenv("LTI_CLIENT_ID", "")
LTI_DEPLOYMENT_ID = os.getenv("LTI_DEPLOYMENT_ID", "")
LTI_PLATFORM_JWKS_URL = os.getenv("LTI_PLATFORM_JWKS_URL", "")
LTI_PLATFORM_AUTHORIZE_URL = os.getenv("LTI_PLATFORM_AUTHORIZE_URL", "")
LTI_REDIRECT_URI = os.getenv("LTI_REDIRECT_URI", "")
