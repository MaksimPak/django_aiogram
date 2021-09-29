"""
Django settings for parcel project.

Generated by 'django-admin startproject' using Django 3.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path

import environ
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(env_file=os.path.join(BASE_DIR, '.env'))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='1123123521312e23421ed3')
APP_ENVIRONMENT = env('APP_ENV', default='development')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG', cast=bool, default=(APP_ENVIRONMENT not
                                         in ('production', 'staging')))


ALLOWED_HOSTS = env('ALLOWED_HOSTS', cast=tuple, default=('0.0.0.0', '127.0.0.1'))


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    'contacts.apps.ContactsConfig',
    'assets.apps.AssetsConfig',
    'courses.apps.CoursesConfig',
    'companies.apps.CompaniesConfig',
    'users.apps.UsersConfig',
    'forms.apps.FormsConfig',
    'broadcast.apps.BroadcastConfig',

    'bootstrap4',
    'flat_json_widget',
    'mapwidgets',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [(os.path.join(BASE_DIR, 'templates'))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'extended': 'general.templatetags'
            },
        },
    },
]

WSGI_APPLICATION = 'app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME', 'parcel'),
        'USER': os.getenv('DB_USER', 'parcel'),
        'PASSWORD': os.getenv('DB_PASS', 'parcel'),
        'HOST': os.getenv('DB_HOST', 'db'),
        'PORT': 5432,
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_L10N = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

# todo this thing will probably break in prod
# https://docs.djangoproject.com/en/3.2/ref/contrib/staticfiles/
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static/'),
]

if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATIC_URL = '/static/'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

# Celery config
CELERY_BROKER_URL = f'redis://{os.getenv("REDIS_HOST", "redis")}:{os.getenv("REDIS_PORT", 6379)}/0'
CELERY_TIMEZONE = 'Asia/Tashkent'
CELERY_RESULT_BACKEND = f'redis://{os.getenv("REDIS_HOST", "redis")}:{os.getenv("REDIS_PORT", 6379)}/0'

# REDIS
REDIS_CUSTOM_DATA = 4

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.getenv('LOG_PATH'),
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

MAP_WIDGETS = {
    "GooglePointFieldWidget": (
        ("zoom", 6),
        ("markerFitZoom", 15),
    ),
    # todo: Achtung! API Key Exposed! (nvm, it is free anyway)
    'GOOGLE_MAP_API_KEY': 'AIzaSyCND4L7d1wxcTyBD04hhJpJFrDT5LXm-8M'
}

if APP_ENVIRONMENT != 'development':
    sentry_sdk.init(
        dsn="https://48a409ab3b5148a8a0d78985db6f9eaa@o437434.ingest.sentry.io/5753954",
        integrations=[DjangoIntegration()],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )
