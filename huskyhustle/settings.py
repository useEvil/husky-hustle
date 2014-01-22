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
SECRET_KEY = 'jillw=2=j97x^+ja$^h-(8v*k4nxpl@09&cv1i7*6r$04ze&2i'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

TEMPLATE_CONTEXT_PROCESSORS = (
    'husky.context_processors.page_content',
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'huskyhustle.urls'

WSGI_APPLICATION = 'huskyhustle.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'husky-hustle.sqlite3'),
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

# Application Constants
DONATION_GOAL     = 50000
MAX_BAR_LENGTH    = 225
MAX_ARROW_HEIGHT  = 275
BASE_ARROW_HEIGHT = 73
RAFFLE_TICKET_AMT = 25

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_PASSWORD = base64.b64decode('')
EMAIL_HOST_USER = 'you@example.com'
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

PAYPAL_PAYPAL_CERT = 'certs/paypal_cert.pem'
PAYPAL_PRIVATE_KEY = 'certs/private_key.pem'
PAYPAL_PUBLIC_KEY = 'certs/public_key.pem'
PAYPAL_IPN_URL = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
PAYPAL_CERT_ID = base64.b64decode('')
PAYPAL_BUS_ID = base64.b64decode('')
PAYPAL_CSV_REPORT = 'data/paypal-report.csv'

PICASA_STORAGE_OPTIONS = {
    'email': 'you@example.com',
    'source': 'example',
    'password': base64.b64decode(''),
    'userid': 'exampleid',
    'cache': True
}
