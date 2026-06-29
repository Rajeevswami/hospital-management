"""
Django settings for hospital_system project.
Environment-driven config: dev uses SQLite fallback, production uses DATABASE_URL (PostgreSQL).
"""

from pathlib import Path
from decouple import config, Csv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------- SECURITY ----------------
SECRET_KEY = config('SECRET_KEY', default='django-insecure-CHANGE-THIS-IN-PRODUCTION')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Auto-detect the free hosting platform's domain (Render, Railway, etc) so you
# don't need to manually edit this every time the platform assigns a new URL.
RENDER_HOSTNAME = config('RENDER_EXTERNAL_HOSTNAME', default='')
if RENDER_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_HOSTNAME}']

# Tells Django to trust the "X-Forwarded-Proto" header from Render/Railway's
# reverse proxy - without this, SECURE_SSL_REDIRECT causes an infinite redirect loop.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ---------------- APPS ----------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'crispy_forms',
    'crispy_bootstrap5',
    'axes',  # brute-force login protection

    # Local apps
    'accounts',
    'patients',
    'doctors',
    'appointments',
    'pharmacy',
    'billing',
    'wards',
    'dashboard',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serves static files fast in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',  # must come after AuthenticationMiddleware
    'core.middleware.AuditContextMiddleware',  # makes current user/IP available to signal handlers
    'core.middleware.IdleSessionTimeoutMiddleware',  # auto-logout after inactivity
    'core.middleware.SecurityHeadersMiddleware',  # extra hardening headers
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hospital_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'hospital_system.wsgi.application'

# ---------------- DATABASE ----------------
# Local dev (no .env DATABASE_URL set) -> SQLite, fast to start.
# Production -> set DATABASE_URL=postgres://user:pass@host:port/dbname
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL', default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,   # persistent connections -> faster requests, no reconnect lag
        conn_health_checks=True,
    )
}

# ---------------- AUTH ----------------
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:home'
LOGOUT_REDIRECT_URL = 'accounts:login'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # checks lockout BEFORE password check
    'django.contrib.auth.backends.ModelBackend',
]

# ---------------- BRUTE-FORCE LOGIN PROTECTION (django-axes) ----------------
AXES_FAILURE_LIMIT = 5            # lock after 5 wrong attempts
AXES_COOLOFF_TIME = 0.5           # unlock automatically after 30 minutes
AXES_LOCKOUT_PARAMETERS = ['username']   # lock per-username, not per-IP (staff share hospital WiFi/IP)
AXES_RESET_ON_SUCCESS = True      # successful login clears the failure counter

# ---------------- IDLE SESSION TIMEOUT ----------------
SESSION_COOKIE_AGE = 1800          # 30 minutes
SESSION_SAVE_EVERY_REQUEST = True  # sliding expiry - resets the 30 min on activity
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
IDLE_TIMEOUT_SECONDS = 1800         # used by core.middleware.IdleSessionTimeoutMiddleware

# ---------------- I18N ----------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ---------------- STATIC / MEDIA ----------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------- CRISPY FORMS ----------------
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# ---------------- PRODUCTION SECURITY (auto-enabled when DEBUG=False) ----------------
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
