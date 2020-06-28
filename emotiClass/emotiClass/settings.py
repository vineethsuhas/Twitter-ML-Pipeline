"""
Django settings for emotiClass project.

Generated by 'django-admin startproject' using Django 1.11.17.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Root directory where the application is located
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

############### PATH SETUP ##################

# Media Root is to store all the media files.
MEDIA_DIR = os.path.abspath(os.path.join(ROOT_DIR, 'media'))
if not os.path.exists(MEDIA_DIR):
    os.mkdir(MEDIA_DIR)

# Temporary storage of any uploads.
UPLOAD_DIR = os.path.abspath(os.path.join(MEDIA_DIR, 'uploads'))
if not os.path.exists(UPLOAD_DIR):
    os.mkdir(UPLOAD_DIR)

# Temporary storage of any uploads.
DATA_DIR = os.path.abspath(os.path.join(MEDIA_DIR, 'data'))
if not os.path.exists(DATA_DIR):
    os.mkdir(DATA_DIR)

# Temporary storage of any uploads.
NRC_LEXICON_DIR = os.path.abspath(os.path.join(MEDIA_DIR, 'nrc_lexicons'))

OFFLINE_SCHEMA_PATH = os.path.abspath(os.path.join(MEDIA_DIR, 'schema'))

# Temporary storage of any uploads.
LOGS_DIR = os.path.abspath(os.path.join(BASE_DIR, '../logs'))
if not os.path.exists(LOGS_DIR):
    os.mkdir(LOGS_DIR)
#############################################

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'z$a4kpk+p9%dcxpx@d*z)g374hak%)82@sc+tb@g_%5&q@b-fh'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'loader'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'emotiClass.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'emotiClass.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(MEDIA_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static")

TWITTER_KAFKA_TOPIC_PREFIX = "tweets_"

ES_IDX_OFFLINE_RAW_PREFIX = 'raw_offline_'
ES_IDX_ONLINE_RAW_PREFIX = 'raw_online_'
ES_IDX_EMOTIONS_PREFIX = 'emotions_'

EC_LOG = 'ec_log'
EC_LOG_FILE = os.path.join(LOGS_DIR, "ec.log")
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': EC_LOG_FILE,
        },
    },
    'loggers': {
        EC_LOG: {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Import the local_settings at the end to override any configuration in local_settings
from emotiClass.config.local_settings import *

