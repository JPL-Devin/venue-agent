import pytest
import jwt
import datetime
import os
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


# ---------------------------------------------------------------------------
# Generate a dedicated RSA key pair for these unit tests (same approach as
# tests/_jwt_env.py).  We do NOT reuse the _jwt_env keys because utils.py
# reads its public key at module‑level import time and _jwt_env already
# wrote the correct public key for it.  Instead we patch
# ``utils.exec_venue_public_pem`` when we need a *different* key (e.g. the
# "wrong key" test).
# ---------------------------------------------------------------------------
_test_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

_test_private_pem = _test_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
).decode()

_test_public_pem = _test_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()

# Re-use the *same* key pair that _jwt_env wrote (and that utils.py loaded).
_env_private_key_path = os.getenv("JWT_PRIVATE_KEY")
if _env_private_key_path:
    _env_private_pem = Path(_env_private_key_path).read_text()
else:
    _env_private_pem = _test_private_pem

import utils  # noqa: E402  – imported after key setup


def _make_token(payload, private_key=_env_private_pem):
    """Helper: create a signed JWT."""
    token = jwt.encode(payload, private_key, algorithm="RS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def _valid_payload(**overrides):
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    base = {
        "sub": "test_user",
        "iat": now,
        "exp": now + 3600,
        "iss": "test_suite",
        "scopes": [{"scope": "execute:testbed"}],
    }
    base.update(overrides)
    return base


# -----------------------------------------------------------------------
# get_decoded_token tests
# -----------------------------------------------------------------------

class TestGetDecodedToken:

    def test_get_decoded_token_valid_bearer(self):
        """Should decode a valid Bearer token successfully."""
        payload = _valid_payload()
        token = _make_token(payload)
        decoded = utils.get_decoded_token(f"Bearer {token}")
        assert decoded["sub"] == "test_user"
        assert decoded["iss"] == "test_suite"

    def test_get_decoded_token_missing_header(self):
        """Should raise when Authorization header is None."""
        with pytest.raises(Exception, match="Authorization header was not provided"):
            utils.get_decoded_token(None)

    def test_get_decoded_token_no_bearer_prefix(self):
        """Should raise when header doesn't start with Bearer."""
        token = _make_token(_valid_payload())
        with pytest.raises(Exception, match="Authorization header should be of format"):
            utils.get_decoded_token(f"Token {token}")

    def test_get_decoded_token_empty_token(self):
        """Should raise when Bearer has no token value."""
        with pytest.raises(Exception, match="Authorization header should be of format"):
            utils.get_decoded_token("Bearer")

    def test_get_decoded_token_invalid_signature(self):
        """Should raise when token signed with wrong key."""
        # Sign with our *separate* test key – utils.py holds a different public key
        payload = _valid_payload()
        bad_token = _make_token(payload, private_key=_test_private_pem)
        with pytest.raises(jwt.exceptions.InvalidSignatureError):
            utils.get_decoded_token(f"Bearer {bad_token}")

    def test_get_decoded_token_expired_token(self):
        """Should raise ExpiredSignatureError for expired token."""
        now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
        payload = _valid_payload(iat=now - 7200, exp=now - 3600)
        token = _make_token(payload)
        with pytest.raises(jwt.exceptions.ExpiredSignatureError):
            utils.get_decoded_token(f"Bearer {token}")


# -----------------------------------------------------------------------
# has_permission tests
# -----------------------------------------------------------------------

class TestHasPermission:

    def test_has_permission_valid_testbed_scope(self):
        """Should return True for execute:testbed scope."""
        decoded = {"scopes": [{"scope": "execute:testbed"}]}
        assert utils.has_permission(decoded) is True

    def test_has_permission_valid_wsts_scope(self):
        """Should return True for execute:wsts scope."""
        decoded = {"scopes": [{"scope": "execute:wsts"}]}
        assert utils.has_permission(decoded) is True

    def test_has_permission_valid_sit_scope(self):
        """Should return True for execute:sit scope."""
        decoded = {"scopes": [{"scope": "execute:sit"}]}
        assert utils.has_permission(decoded) is True

    def test_has_permission_valid_other_scope(self):
        """Should return True for execute:other scope."""
        decoded = {"scopes": [{"scope": "execute:other"}]}
        assert utils.has_permission(decoded) is True

    def test_has_permission_empty_scopes(self):
        """Should return False when scopes is empty list."""
        decoded = {"scopes": []}
        assert utils.has_permission(decoded) is False

    def test_has_permission_no_scope_key(self):
        """Should return False when scope dicts have no 'scope' key."""
        decoded = {"scopes": [{"name": "execute:testbed"}]}
        assert utils.has_permission(decoded) is False

    def test_has_permission_invalid_scope(self):
        """Should return False when scope not in accepted list."""
        decoded = {"scopes": [{"scope": "execute:unknown"}]}
        assert utils.has_permission(decoded) is False

    def test_has_permission_legacy_string_scope(self):
        """Should handle legacy string format scopes (not dict)."""
        decoded = {"scopes": ["execute:testbed"]}
        assert utils.has_permission(decoded) is True

    def test_has_permission_multiple_scopes_one_valid(self):
        """Should return True if at least one scope matches."""
        decoded = {"scopes": [
            {"scope": "read:data"},
            {"scope": "execute:sit"},
        ]}
        assert utils.has_permission(decoded) is True

    def test_has_permission_no_scopes_key(self):
        """Should return False when jwt_decoded has no 'scopes' key."""
        decoded = {"sub": "test_user"}
        assert utils.has_permission(decoded) is False
