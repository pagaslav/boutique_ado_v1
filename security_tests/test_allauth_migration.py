"""Allauth upgrade regressions on synthetic users and disposable databases."""
import re
from urllib.parse import urlsplit
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core import mail
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, RequestFactory, TestCase, TransactionTestCase, override_settings
from allauth.account.models import EmailAddress
from allauth.core.internal.httpkit import get_client_ip

PAGE_STORAGES = {**settings.STORAGES, 'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'}}
TEST_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'allauth-upgrade-tests'}}

@override_settings(STORAGES=PAGE_STORAGES, CACHES=TEST_CACHE)
class AllauthAccountTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.password = 'SyntheticM!gration-Password742'

    def create_user(self, verified=True, staff=False):
        user = get_user_model().objects.create_user(username='migration-user', email='migration@example.invalid', password=self.password, is_staff=staff)
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=verified)
        return user

    def test_login_signup_password_reset_pages_and_csrf(self):
        for name in ('login', 'signup', 'password/reset'):
            response = self.client.get('/accounts/' + name + '/')
            self.assertEqual(response.status_code, 200, name)
        client = Client(enforce_csrf_checks=True)
        response = client.post('/accounts/login/', {'login': 'nobody', 'password': 'wrong'})
        self.assertEqual(response.status_code, 403)

    def test_verified_user_login_and_untrusted_next_redirect(self):
        user = self.create_user()
        response = self.client.post('/accounts/login/', {'login': user.email, 'password': self.password, 'next': 'https://attacker.example.invalid/'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(str(self.client.session['_auth_user_id']), str(user.pk))
        self.assertFalse(response['Location'].startswith('https://attacker.example.invalid/'))
        self.assertEqual(self.client.post('/accounts/logout/').status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_staff_admin_login_survives_backend_change(self):
        user = self.create_user(staff=True)
        response = self.client.post('/admin/login/?next=/admin/', {'username': user.username, 'password': self.password, 'next': '/admin/'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(str(self.client.session['_auth_user_id']), str(user.pk))

    def test_unverified_email_cannot_establish_authenticated_session(self):
        user = self.create_user(verified=False)
        response = self.client.post('/accounts/login/', {'login': user.email, 'password': self.password})
        self.assertIn(response.status_code, (200, 302))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_signup_preserves_email_confirmation_and_profile(self):
        payload = {'username': 'new-migration-user', 'email': 'new@example.invalid', 'password1': self.password, 'password2': self.password, 'first_name': 'Synthetic', 'last_name': 'User', 'street_address1': 'Test Street', 'town_city': 'Test City', 'country': 'GB'}
        if 'email2*' in settings.ACCOUNT_SIGNUP_FIELDS:
            payload['email2'] = payload['email']
        response = self.client.post('/accounts/signup/', payload)
        self.assertEqual(response.status_code, 302, getattr(response, 'context', None))
        user = get_user_model().objects.get(username=payload['username'])
        self.assertTrue(user.check_password(self.password))
        self.assertTrue(EmailAddress.objects.filter(user=user, email=payload['email'], verified=False).exists())
        self.assertNotIn('_auth_user_id', self.client.session)
        from profiles.models import UserProfile
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
        self.assertGreaterEqual(len(mail.outbox), 1)

    def test_password_reset_round_trip_with_local_mail(self):
        user = self.create_user()
        response = self.client.post('/accounts/password/reset/', {'email': user.email})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(r'https?://[^\s]+/accounts/password/reset/key/[^\s]+', mail.outbox[0].body)
        self.assertIsNotNone(match)
        path = urlsplit(match.group(0)).path
        response = self.client.get(path)
        self.assertEqual(response.status_code, 302)
        path = response['Location']
        response = self.client.post(path, {'password1': 'ReplacedSyntheticPassword!925', 'password2': 'ReplacedSyntheticPassword!925'})
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password('ReplacedSyntheticPassword!925'))
        self.assertFalse(user.check_password(self.password))

    def test_forged_forwarding_header_cannot_select_rate_limit_identity(self):
        factory = RequestFactory()
        for forwarded in ('198.51.100.2', '198.51.100.3'):
            request = factory.get('/accounts/login/', REMOTE_ADDR='192.0.2.10', HTTP_X_FORWARDED_FOR=forwarded)
            self.assertEqual(get_client_ip(request), '192.0.2.10')

class LegacyEmailMigrationTests(TransactionTestCase):
    def test_existing_email_user_id_password_and_profile_survive_schema_upgrade(self):
        targets = MigrationExecutor(connection).loader.graph.leaf_nodes()
        try:
            executor = MigrationExecutor(connection)
            executor.migrate([('account', '0005_emailaddress_idx_upper_email')])
            apps = executor.loader.project_state([('account', '0005_emailaddress_idx_upper_email')]).apps
            User = apps.get_model('auth', 'User')
            Address = apps.get_model('account', 'EmailAddress')
            password = make_password('SyntheticLegacyPassword!531')
            user = User.objects.create(username='legacy-migration', email='Legacy@EXAMPLE.INVALID', password=password)
            address = Address.objects.create(user_id=user.pk, email='Legacy@EXAMPLE.INVALID', verified=True, primary=True)
            # Historical model creation does not run current profile signals.
            from profiles.models import UserProfile
            profile = UserProfile.objects.create(user_id=user.pk)
            MigrationExecutor(connection).migrate(targets)
            current = get_user_model().objects.get(pk=user.pk)
            self.assertEqual(current.password, password)
            self.assertTrue(current.check_password('SyntheticLegacyPassword!531'))
            self.assertEqual(current.email, 'legacy@example.invalid')
            migrated = EmailAddress.objects.get(pk=address.pk)
            self.assertTrue(migrated.verified)
            self.assertTrue(migrated.primary)
            self.assertEqual(migrated.user_id, user.pk)
            self.assertEqual(migrated.email, 'legacy@example.invalid')
            from profiles.models import UserProfile
            self.assertEqual(UserProfile.objects.get(user_id=user.pk).pk, profile.pk)
        finally:
            MigrationExecutor(connection).migrate(targets)
