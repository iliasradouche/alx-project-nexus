"""
Django settings for movie_backend project.
"""

from pathlib import Path
import os
from decouple import config
from datetime import timedelta
import sys

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core security / debug ---
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)

# Tell Django it sits behind Railway’s proxy (TLS ends at the proxy)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".railway.app",  # any subdomain of railway.app
    "alx-project-nexus-production-f78f.up.railway.app",  # explicit host
    "project-nexus-alx.netlify.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://project-nexus-alx.netlify.app",
    "https://*.netlify.app",
]

# --- Apps ---
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "drf_yasg",
    "corsheaders",
    "django_extensions",
    "movies",
]

# --- Middleware ---
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # keep at the very top
    "django.middleware.security.SecurityMiddleware",
    "movies.middleware.SecurityHeadersMiddleware",
    "movies.middleware.RequestValidationMiddleware",
    "movies.middleware.RateLimitMiddleware",
    # "django.middleware.cache.UpdateCacheMiddleware",  # disabled while fixing CORS
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "movies.middleware.ErrorLoggingMiddleware",
    "movies.middleware.APIResponseCacheMiddleware",
    "movies.middleware.PerformanceMonitoringMiddleware",
    "movies.middleware.RequestResponseLoggingMiddleware",
    # "django.middleware.cache.FetchFromCacheMiddleware",  # disabled while fixing CORS
]

ROOT_URLCONF = "movie_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "movie_backend.wsgi.application"

# --- Database (SQLite default) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {'timeout': 20, 'check_same_thread': False},
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }
}

# --- Password validation ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18N ---
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# --- Static files ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- TMDb ---
TMDB_API_KEY = config('TMDB_API_KEY', default='826a3a3839ec63b88984d8f5becfc10d')
TMDB_BASE_URL = config('TMDB_BASE_URL', default='https://api.themoviedb.org/3')

# --- DRF ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'movies.exceptions.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

# --- JWT ---
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# --- CORS ---
CORS_ALLOWED_ORIGINS = [
    "https://project-nexus-alx.netlify.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
# Allow Netlify preview subdomains too (e.g., https://deploy-preview-123--*.netlify.app)
CORS_ALLOWED_ORIGIN_REGEXES = [r"^https://.*\.netlify\.app$"]

CORS_ALLOW_CREDENTIALS = True  # keep True only if you actually use cookies

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']

# --- Cache (dummy while debugging CORS) ---
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'movie_rec'

# --- Logging ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}', 'style': '{'},
        'simple': {'format': '{levelname} {message}', 'style': '{'},
    },
    'handlers': {
        'file': {'level': 'INFO', 'class': 'logging.FileHandler', 'filename': BASE_DIR / 'logs' / 'django.log', 'formatter': 'verbose'},
        'error_file': {'level': 'ERROR', 'class': 'logging.FileHandler', 'filename': BASE_DIR / 'logs' / 'error.log', 'formatter': 'verbose'},
        'console': {'level': 'INFO', 'class': 'logging.StreamHandler', 'formatter': 'simple'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
    'loggers': {
        'django': {'handlers': ['file', 'console'], 'level': 'INFO', 'propagate': False},
        'movies': {'handlers': ['file', 'error_file', 'console'], 'level': 'INFO', 'propagate': False},
    },
}

LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# --- Security headers ---
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# --- Rate limits / misc ---
API_RATE_LIMIT = {'REQUESTS_PER_MINUTE': 100, 'REQUESTS_PER_HOUR': 1000, 'REQUESTS_PER_DAY': 10000}
ERROR_HANDLING = {'LOG_ERRORS': True, 'SEND_ERROR_EMAILS': False, 'ERROR_EMAIL_RECIPIENTS': []}

# --- API Docs ---
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {'Bearer': {'type': 'apiKey', 'name': 'Authorization', 'in': 'header'}},
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': ['get', 'post', 'put', 'delete', 'patch'],
    'OPERATIONS_SORTER': 'alpha',
    'TAGS_SORTER': 'alpha',
    'DOC_EXPANSION': 'none',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'SHOW_COMMON_EXTENSIONS': True,
}
REDOC_SETTINGS = {'LAZY_RENDERING': False}

# --- Cookie settings for cross-origin (only needed if using cookies from browser) ---
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'
CSRF_COOKIE_SAMESITE = 'None' if not DEBUG else 'Lax'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
