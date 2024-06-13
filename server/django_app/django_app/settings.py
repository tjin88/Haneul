"""
Django settings for django_app project.

Generated by 'django-admin startproject' using Django 4.1.13.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

from pathlib import Path
from decouple import config
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
from corsheaders.defaults import default_headers

load_dotenv()  # Load environment variables from .env file

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')

JWT_TOKEN = quote_plus(os.getenv('JWT_TOKEN'))

# SECURITY WARNING: don't run with debug turned on in production!
# TODO: Change this to False for production
DEBUG = True

# TODO: Add domain here when deploying
ALLOWED_HOSTS = ['127.0.0.1', 'haneul.onrender.com']

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'centralized_API_backend',
    'rest_framework',
    'corsheaders',
]

# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.TokenAuthentication',
#         'rest_framework.authentication.SessionAuthentication',
#     ],
#     'DEFAULT_PERMISSION_CLASSES': [
#         'rest_framework.permissions.IsAuthenticated',
#     ],
# }

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    'X-User-Email',
    'X-CSRFToken',
    'Content-Type',
]

# TODO: REMOVE THIS BEFORE DEPLOYING*****
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     # TODO: Add production frontend domain when deploying**
# ]

# TODO: Add CSRF trusted origins when deploying
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    # Add your production frontend domain here
]

ROOT_URLCONF = "django_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "django_app.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

# Testing with local database (db.sqlite3)
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

# username = quote_plus(os.getenv('USERNAME'))
# password = quote_plus(os.getenv('PASSWORD'))
# cluster = os.getenv('CLUSTER')
# DATABASES = {
#     'default': {
#         'ENGINE': 'djongo',
#         'NAME': 'SCRAPED_MANGA_AND_LIGHTNOVEL_DATABASE',
#         'ENFORCE_SCHEMA': False,
#         'CLIENT': {
#             'host': f"mongodb+srv://{username}:{password}@{cluster}/?retryWrites=true&w=majority"
#         }
#     }
# }

# # PostgreSQL (Local)
# postgresql_name = os.getenv('postgresql_local_name')
# postgresql_user = os.getenv('postgresql_local_user')
# postgresql_password = os.getenv('postgresql_local_password')
# postgresql_host = os.getenv('postgresql_local_host')
# postgresql_port = os.getenv('postgresql_local_port')

# PostgreSQL (Supabase)
postgresql_name = os.getenv('postgresql_supabase_name')
postgresql_user = os.getenv('postgresql_supabase_user')
postgresql_password = os.getenv('postgresql_supabase_password')
postgresql_host = os.getenv('postgresql_supabase_host')
postgresql_port = os.getenv('postgresql_supabase_port')

# PostgreSQL (regardless of local or Supabase)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': postgresql_name,
        'USER': postgresql_user,
        'PASSWORD': postgresql_password,
        'HOST': postgresql_host,
        'PORT': postgresql_port,
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

USE_I18N = True

USE_TZ = True
TIME_ZONE = 'America/New_York'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
