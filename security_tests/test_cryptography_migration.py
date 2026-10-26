"""Generated keys and tokens only; no application secrets or network."""
import datetime
import unittest
import jwt
from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509.oid import NameOID

class CryptoCompatibilityTests(unittest.TestCase):
    def test_existing_fernet_tokens_remain_readable_and_tampering_is_rejected(self):
        # Public synthetic fixture generated with cryptography 43; never a real key.
        fernet = Fernet(b'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=')
        token = b'gAAAAABq3ylALlKMGUcLEXw7T46kvvXvowTreVXXVisKhmvnU82p7JvJrnBWi61tYNOGddLekAVpxwJsyn8hUcaweUcnyzlPlUTl0i86X9TUysrwFwu4kVU='
        self.assertEqual(fernet.decrypt(token), b'synthetic migration fixture')
        with self.assertRaises(InvalidToken):
            fernet.decrypt(token[:-2] + b'xx')

    def test_rsa_pem_and_jwt_signatures_remain_compatible(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.BestAvailableEncryption(b'synthetic-passphrase'))
        loaded = serialization.load_pem_private_key(pem, password=b'synthetic-passphrase')
        signature = loaded.sign(b'synthetic payload', padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        key.public_key().verify(signature, b'synthetic payload', padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        with self.assertRaises(InvalidSignature):
            key.public_key().verify(signature, b'changed payload', padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
        token = jwt.encode({'sub': 'synthetic-user', 'aud': 'synthetic-client'}, key, algorithm='RS256')
        self.assertEqual(jwt.decode(token, key.public_key(), algorithms=['RS256'], audience='synthetic-client')['sub'], 'synthetic-user')
        with self.assertRaises(jwt.InvalidAudienceError):
            jwt.decode(token, key.public_key(), algorithms=['RS256'], audience='wrong-client')

    def test_x509_certificate_round_trip(self):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'synthetic.example.invalid')])
        now = datetime.datetime.now(datetime.timezone.utc)
        certificate = x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(1).not_valid_before(now - datetime.timedelta(days=1)).not_valid_after(now + datetime.timedelta(days=1)).sign(key, hashes.SHA256())
        parsed = x509.load_pem_x509_certificate(certificate.public_bytes(serialization.Encoding.PEM))
        self.assertEqual(parsed.subject, name)
        key.public_key().verify(parsed.signature, parsed.tbs_certificate_bytes, padding.PKCS1v15(), parsed.signature_hash_algorithm)
