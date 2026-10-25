"""Migrations and authentication run only against a disposable in-memory DB."""
import django
from django.conf import settings
from django.contrib.auth import get_user_model, authenticate
from django.test import TestCase, Client

class UpgradeSmokeTests(TestCase):
    def test_patched_django_and_isolated_database(self):
        self.assertEqual(django.VERSION[:3], (5, 2, 18))
        self.assertIn('memory', str(settings.DATABASES['default']['NAME']))
        self.assertFalse(settings.DEBUG)

    def test_user_password_and_session_round_trip(self):
        user = get_user_model().objects.create_user(username='security-smoke', email='security@example.invalid', password='TestPassword1')
        self.assertNotEqual(user.password, 'TestPassword1')
        self.assertEqual(authenticate(username='security-smoke', password='TestPassword1').pk, user.pk)
        self.assertIsNone(authenticate(username='security-smoke', password='wrong'))
        self.assertTrue(self.client.login(username='security-smoke', password='TestPassword1'))
        self.assertIn('_auth_user_id', self.client.session)
        self.client.logout()
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_admin_requires_authentication_and_csrf(self):
        self.assertEqual(self.client.get('/admin/').status_code, 302)
        self.assertEqual(Client(enforce_csrf_checks=True).post('/admin/login/', {'username': 'x', 'password': 'y'}).status_code, 403)

    def test_aws_backends_and_false_development_flag(self):
        import os, runpy
        from pathlib import Path
        from unittest.mock import patch
        with patch.dict(os.environ, {'USE_AWS': '1', 'DEVELOPMENT': 'False'}):
            configured = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'boutique_ado/settings.py'))
        self.assertFalse(configured['DEBUG'])
        self.assertEqual(configured['STORAGES']['default']['BACKEND'], 'custom_storages.MediaStorage')
        self.assertEqual(configured['STORAGES']['staticfiles']['BACKEND'], 'custom_storages.StaticStorage')

    def test_profile_signal_creates_exactly_one_profile_without_breaking_transaction(self):
        from profiles.models import UserProfile
        user = get_user_model().objects.create_user(username='profile-smoke')
        user.first_name = 'Updated'
        user.save()
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
        self.assertEqual(get_user_model().objects.get(pk=user.pk).first_name, 'Updated')
