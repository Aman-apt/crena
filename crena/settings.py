import os
from pathlib import Path
from dotenv import load_dotenv

#import module syst to get the type of exception
import sys
import urllib.parse as urlparse

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "onlyuseindsedenv")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

AUTH_USER_MODEL = 'core.User'


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # health check apps
    'health_check',
    
    # local apps
    'analytics',
    'api',
    'core',
    'dashboard',

    # third-party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'rest_framework',
    'corsheaders',
    'rules', 
    'debug_toolbar',
    'django_user_agents',
]

SITE_ID = 1

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware', # corsheaders middlwares
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware', # allauth configs 
    'debug_toolbar.middleware.DebugToolbarMiddleware', 
    'django_user_agents.middleware.UserAgentMiddleware'
]

ROOT_URLCONF = 'crena.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'crena.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Password Validators 

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Other allauth settings
ACCOUNT_EMAIL_VERIFICATION = 'none'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = True  

# Celery and Redis configurations > comment it if using dokcer container 
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Service related constants and varilables
SCRIPT_HEARTBEAT_FREQUENCY = int("5000")

#MaxMind Configs 
MAXMIND_CITY_DB = os.path.join("..analytics/geoip2/GeoLite2-City_20250916/GeoLite2-City.mmdb")
MAXMIND_ASN_DB = os.path.join("..analytics/geoip2/GeoLite2-City_20250916/GeoLite2-ASN.mmdb")
MAXMIND_COUNTRY_DB = os.path.join("..analytics/geoip2/GeoLite2-City_20250916/GeoLite2-Country.mmdb")


#To be Added in the env
ONLY_SUPERUSERS_CREATE = True
SCRIPT_USE_HTTPS = True
SCRIPT_HEARTBEAT_FREQUENCY = 5000
SESSION_MEMORY_TIMEOUT = 1800
SHOW_SHYNET_VERSION = True
SHOW_THIRD_PARTY_ICONS = True
BLOCK_ALL_IPS = False
AGGRESSIVE_HASH_SALTING = False
LOCATION_URL = "https://www.openstreetmap.org/?mlat=$LATITUDE&mlon=$LONGITUDE"
DASHBOARD_PAGE_SIZE = 5
USE_RELATIVE_MAX_IN_BAR_VISUALIZATION = True

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = ["GET", "OPTIONS"]


# Logging confiugrations 
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # Keep the default Django loggers enabled
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'ERROR',  # Log ERROR and above to file
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'error.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        # Add your application loggers here
        'analytics': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'api': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'core': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'dashboard': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
