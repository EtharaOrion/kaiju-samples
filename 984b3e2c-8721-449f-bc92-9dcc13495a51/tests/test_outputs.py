"""Behavioral tests for oauthlib.common (restoration task).

These import the real solution module and assert on concrete behavior
described in TRUTH.md's contract. They are designed to pass on a correct
implementation and fail on stubbed/broken ones.
"""
import pytest

# The solution module is oauthlib.common; import it robustly.
try:
    from common import (
        quote, unquote, urldecode, Request, CaseInsensitiveDict,
        to_unicode, generate_signed_token, verify_signed_token,
        urlencode,
    )
    import common as common_mod
except ImportError:  # pragma: no cover - fallback for package layout
    from oauthlib.common import (
        quote, unquote, urldecode, Request, CaseInsensitiveDict,
        to_unicode, generate_signed_token, verify_signed_token,
        urlencode,
    )
    import oauthlib.common as common_mod


# ---------------------------------------------------------------------------
# quote / unquote
# ---------------------------------------------------------------------------











# ---------------------------------------------------------------------------
# urldecode
# ---------------------------------------------------------------------------















# ---------------------------------------------------------------------------
# to_unicode
# ---------------------------------------------------------------------------









# ---------------------------------------------------------------------------
# CaseInsensitiveDict
# ---------------------------------------------------------------------------







# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------













# ---------------------------------------------------------------------------
# generate_signed_token / verify_signed_token roundtrip (JWT RS256)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rsa_keys():
    pytest.importorskip("cryptography")
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def _make_token_request():
    class FakeReq:
        expires_in = 3600
        scopes = ["read", "write"]
        claims = {"custom": "value"}

        def __init__(self):
            self.scope = "read write"
    return FakeReq()


def test_request_uri_query():
    r = Request("http://example.com/path?a=1&b=2")
    assert r.uri_query == "a=1&b=2"

def test_request_uri_query_params():
    r = Request("http://example.com/path?a=1&b=2")
    params = r.uri_query_params
    assert ("a", "1") in params
    assert ("b", "2") in params

def test_request_uri_query_params_empty_no_query():
    # Must short-circuit to [] instead of raising via strict parse_qsl.
    r = Request("http://example.com/path")
    assert r.uri_query_params == []

def test_request_duplicate_params_none_body_safe():
    # body defaults to None-ish; must not crash.
    r = Request("http://example.com/path?a=1&a=2")
    dup = r.duplicate_params
    assert "a" in dup

def test_request_duplicate_params_across_body_and_query():
    r = Request("http://example.com/path?a=1", body="a=2&b=3")
    assert "a" in r.duplicate_params
    assert "b" not in r.duplicate_params

def test_request_no_duplicates():
    r = Request("http://example.com/path?a=1&b=2", body="c=3")
    assert r.duplicate_params == []

def test_generate_signed_token_returns_unicode(rsa_keys):
    pytest.importorskip("jwt")
    priv_pem, _ = rsa_keys
    req = _make_token_request()
    token = generate_signed_token(priv_pem, req)
    assert isinstance(token, str)
    # JWT is three base64url segments separated by dots.
    assert token.count(".") == 2

def test_signed_token_roundtrip_claims(rsa_keys):
    pytest.importorskip("jwt")
    priv_pem, pub_pem = rsa_keys
    req = _make_token_request()
    token = generate_signed_token(priv_pem, req)
    claims = verify_signed_token(pub_pem, token)
    assert isinstance(claims, dict)
    assert "scope" in claims
    assert "exp" in claims
    # merged custom claim from request.claims
    assert claims.get("custom") == "value"

def test_verify_signed_token_rejects_tampered(rsa_keys):
    pytest.importorskip("jwt")
    import jwt as _jwt
    priv_pem, pub_pem = rsa_keys
    req = _make_token_request()
    token = generate_signed_token(priv_pem, req)
    # Tamper with the payload segment.
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1][:-3] + "AAA" + "." + parts[2]
    with pytest.raises(Exception):
        verify_signed_token(pub_pem, tampered)
