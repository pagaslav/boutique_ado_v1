"""Keep generated environments out of the versioned application source."""
import subprocess
from pathlib import Path
from django.test import SimpleTestCase

class SourceEnvironmentTests(SimpleTestCase):
    def test_no_generated_environment_is_tracked(self):
        root = Path(__file__).resolve().parents[1]
        tracked = subprocess.run(['git', 'ls-files', '--', 'venv/', '.venv/'], cwd=root, check=True, capture_output=True, text=True).stdout
        self.assertEqual(tracked, '', 'Create a fresh local/staging environment from requirements.txt; do not commit its installed packages.')
        ignored = (root / '.gitignore').read_text().splitlines()
        self.assertIn('venv/', ignored)
        self.assertIn('.venv/', ignored)
