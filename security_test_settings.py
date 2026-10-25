"""Disposable CI only. Never import this module from production entry points."""
import os
os.environ.setdefault('SECRET_KEY', 'security-ci-only-not-a-real-secret')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
from boutique_ado.settings import *
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
SECRET_KEY = 'security-ci-only-not-a-real-secret'
DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost']
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
STATICFILES_DIRS = []
