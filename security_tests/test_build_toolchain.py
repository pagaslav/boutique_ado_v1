"""Build an artificial package offline with the installed setuptools backend."""
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from django.test import SimpleTestCase

class BuildToolchainTests(SimpleTestCase):
    def test_local_wheel_build_with_modern_setuptools(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'pyproject.toml').write_text('[build-system]\nrequires = ["setuptools==84.2.1", "wheel"]\nbuild-backend = "setuptools.build_meta"\n[project]\nname = "security-build-fixture"\nversion = "0.0.1"\n')
            (root/'fixture.py').write_text('ANSWER = 42\n')
            result = subprocess.run([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--no-build-isolation', '--no-index', '--wheel-dir', str(root/'dist'), str(root)], cwd=root, env=dict(os.environ, PIP_CONFIG_FILE=os.devnull), capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            wheel, = (root/'dist').glob('*.whl')
            with zipfile.ZipFile(wheel) as built:
                self.assertEqual(built.read('fixture.py'), b'ANSWER = 42\n')
                self.assertTrue(any(name.endswith('.dist-info/METADATA') for name in built.namelist()))

    def test_country_address_form_and_storage_code(self):
        from checkout.forms import OrderForm
        from django_countries.fields import Country
        form = OrderForm(data={'full_name': 'Synthetic Buyer', 'email': 'buyer@example.invalid', 'phone_number': '+441234567890', 'country': 'GB', 'postcode': 'SW1A 1AA', 'town_or_city': 'London', 'street_address1': 'Test Street', 'street_address2': '', 'county': ''})
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self.assertEqual(str(form.cleaned_data['country']), 'GB')
        order = form.save(commit=False)
        self.assertEqual(order.country.code, 'GB')
        self.assertEqual(Country(code='GB').name, 'United Kingdom')
        invalid = OrderForm(data={**form.data, 'country': 'ZZ'})
        self.assertFalse(invalid.is_valid())
        self.assertIn('country', invalid.errors)
