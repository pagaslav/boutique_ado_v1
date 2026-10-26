"""Small synthetic images only; no real uploads or external storage."""
import io
import unittest
from unittest.mock import patch
from PIL import Image, UnidentifiedImageError
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

class ImageCompatibilityTests(unittest.TestCase):
    def test_png_and_jpeg_decode_and_django_image_validation(self):
        for fmt in ('PNG', 'JPEG'):
            with self.subTest(format=fmt):
                buffer = io.BytesIO()
                Image.new('RGB', (12, 8), '#2468ac').save(buffer, format=fmt)
                raw = buffer.getvalue()
                with Image.open(io.BytesIO(raw), formats=['PNG', 'JPEG']) as image:
                    image.load()
                    self.assertEqual(image.size, (12, 8))
                cleaned = forms.ImageField().clean(SimpleUploadedFile('test.' + fmt.lower(), raw))
                self.assertEqual(cleaned.image.format, fmt)

    def test_invalid_and_truncated_uploads_are_rejected(self):
        buffer = io.BytesIO()
        Image.new('RGB', (8, 8)).save(buffer, format='PNG')
        for data in (b'not an image', buffer.getvalue()[:20]):
            with self.assertRaises(ValidationError):
                forms.ImageField().clean(SimpleUploadedFile('test.png', data))

    def test_pixel_limits_are_preserved_and_bombs_rejected_without_large_allocation(self):
        self.assertIsNotNone(Image.MAX_IMAGE_PIXELS)
        buffer = io.BytesIO()
        Image.new('RGB', (16, 16)).save(buffer, format='PNG')
        with patch.object(Image, 'MAX_IMAGE_PIXELS', 8):
            with self.assertRaises(ValidationError):
                forms.ImageField().clean(SimpleUploadedFile('test.png', buffer.getvalue()))
