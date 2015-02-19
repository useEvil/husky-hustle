"""
Django settings for huskyhustle project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import base64

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False
TEMPLATE_DIRS = (os.path.join(BASE_DIR, 'huskyhustle/husky/templates'))

MEDIA_ROOT = 'husky/static'
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/'

ALLOWED_HOSTS = [
    'huskyhustle.com'
]

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sites',
#     'djangorestframework',
#     'django_mobile',
    'import_export',
    'pipeline',
    'changuito',
    'picasa',
    'husky',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'changuito.middleware.CartMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    # 'django_mobile.context_processors.flavour',

    # Application context processors
    'husky.context_processors.page_content',
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

ROOT_URLCONF = 'huskyhustle.urls'

WSGI_APPLICATION = 'huskyhustle.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'husky-hustle.db'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

SITE_ID = 3

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

# Static CSS and JS file compression
#PIPELINE = True
#PIPELINE_STORAGE = 'pipeline.storage.PipelineFinderStorage'
#STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
#PIPELINE_CSS = {
#    'huskyhustle': {
#        'source_filenames': (
#            'css/husky-hustle.css',
#        ),
#        'output_filename': 'css/husky-hustle.min.css',
#    },
#}

#PIPELINE_JS = {
#    'huskyhustle': {
#        'source_filenames': (
#            'js/husky-hustle.js',
#        ),
#        'output_filename': 'js/husky-hustle.min.js',
#    }
#}

# Application Constants
DONATION_GOAL     = 50000
MAX_BAR_LENGTH    = 225
MAX_ARROW_HEIGHT  = 275
BASE_ARROW_HEIGHT = 73
RAFFLE_TICKET_AMT = 25

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_PASSWORD = base64.b64decode('')
EMAIL_HOST_USER = 'email@example.com'
EMAIL_SUBJECT_PREFIX = 'HH: '
EMAIL_USE_TLS = True

FACEBOOK_APP_ID = ''
FACEBOOK_SECRET_KEY = ''
FACEBOOK_REQUEST_PERMISSIONS = ''

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET_KEY = ''
TWITTER_REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
TWITTER_AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

BITLY_LOGIN = ''
BITLY_APIKEY = ''

# PayPal BUTTON API CONSTANTS
PAYPAL_PAYPAL_CERT = 'certs/paypal_cert.pem'
PAYPAL_PRIVATE_KEY = 'certs/private_key.pem'
PAYPAL_PUBLIC_KEY = 'certs/public_key.pem'
PAYPAL_IPN_URL = 'https://www.paypal.com/cgi-bin/webscr'
PAYPAL_CERT_ID = base64.b64decode('')
PAYPAL_BUS_ID = base64.b64decode('')
PAYPAL_REST_API = 'https://api.sandbox.paypal.com'
PAYPAL_CSV_REPORT = 'data/paypal-report.csv'

# PayPal REST API CONSTANTS
PAYPAL_REST_API_ACCOUNT = ''
PAYPAL_REST_API_ENDPOINT = 'https://api.paypal.com'
PAYPAL_REST_API_CLIENT_ID = base64.b64decode('')
PAYPAL_REST_API_SECTRET = base64.b64decode('')
PAYPAL_REST_API_ACCESS_TOKEN = base64.b64decode('')
PAYPAL_REST_API_APP_ID = base64.b64decode('')

PICASA_STORAGE_OPTIONS = {
    'email': 'email@example.com',
    'source': 'example_source',
    'password': base64.b64decode(''),
    'userid': 'example_user',
    'cache': True
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/husky-hustle-error.log',
        },
    },
    'loggers': {
        'husky': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
