#!/usr/bin/env python3
"""
Test suite for JWT token signature validation.
Verifies that tokens can be created and verified with the current keys.
"""

import os
import json
import sys
import urllib.request
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import jwt
import base64

load_dotenv()

def int_to_base64url(val: int, length: int) -> str:
    bytes_val = val.to_bytes(length, byteorder='big')
    return base64.urlsafe_b64encode(bytes_val).rstrip(b'=').decode('ascii')

def test_keys_match():
    """Test that server JWKS matches the saved private key."""
    print("\n🔍 Test 1: Keys Match")
    print("=" * 50)

    # Get JWKS from server
    try:
        with urllib.request.urlopen('http://localhost:3000/.well-known/jwks.json') as r:
            jwks = json.loads(r.read())
            server_n = jwks['keys'][0]['n']
    except Exception as e:
        print(f"❌ Failed to fetch JWKS from server: {e}")
        return False

    # Load private key and extract public key
    try:
        with open('private_key.pem', 'r') as f:
            private_pem = f.read()

        private_key = serialization.load_pem_private_key(
            private_pem.encode(),
            password=None,
            backend=default_backend()
        )

        public_numbers = private_key.public_key().public_numbers()
        file_n = int_to_base64url(public_numbers.n, (public_numbers.n.bit_length() + 7) // 8)
    except Exception as e:
        print(f"❌ Failed to load private key: {e}")
        return False

    if server_n == file_n:
        print(f"✅ Keys match!")
        print(f"   Modulus (first 50): {server_n[:50]}")
        return True
    else:
        print(f"❌ Keys DO NOT match!")
        print(f"   Server: {server_n[:50]}")
        print(f"   File:   {file_n[:50]}")
        return False

def test_token_signature():
    """Test that we can create and verify a JWT token."""
    print("\n🔍 Test 2: Token Signature")
    print("=" * 50)

    from aws_sts import create_oidc_jwt, load_private_key_from_file

    # Get env vars
    user_id = os.getenv('AWS_USER_ID', 'magic:mahesh')
    issuer = os.getenv('ISSUER', 'https://oidc.awanipro.com')

    # Load private key
    try:
        private_key_pem = load_private_key_from_file('private_key.pem')
    except Exception as e:
        print(f"❌ Failed to load private key: {e}")
        return False

    # Create JWT
    try:
        token = create_oidc_jwt(private_key_pem, user_id, issuer=issuer)
        print(f"✅ JWT created successfully")
        print(f"   Token (first 50): {token[:50]}...")
    except Exception as e:
        print(f"❌ Failed to create JWT: {e}")
        return False

    # Load public key from private key
    try:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
    except Exception as e:
        print(f"❌ Failed to extract public key: {e}")
        return False

    # Verify token signature
    try:
        decoded = jwt.decode(token, public_key_pem, algorithms=['RS256'], options={'verify_aud': False})
        print(f"✅ Token signature is VALID")
        print(f"   Payload: {json.dumps(decoded, indent=2, default=str)}")
        return True
    except Exception as e:
        print(f"❌ Token signature is INVALID: {e}")
        return False

def test_jwks_format():
    """Test that JWKS has correct format."""
    print("\n🔍 Test 3: JWKS Format")
    print("=" * 50)

    try:
        with urllib.request.urlopen('http://localhost:3000/.well-known/jwks.json') as r:
            jwks = json.loads(r.read())
    except Exception as e:
        print(f"❌ Failed to fetch JWKS: {e}")
        return False

    # Check structure
    if 'keys' not in jwks:
        print(f"❌ JWKS missing 'keys' field")
        return False

    if not jwks['keys']:
        print(f"❌ JWKS keys array is empty")
        return False

    key = jwks['keys'][0]
    required_fields = ['kty', 'use', 'kid', 'n', 'e', 'alg']
    missing = [f for f in required_fields if f not in key]

    if missing:
        print(f"❌ JWKS key missing fields: {missing}")
        return False

    print(f"✅ JWKS format is valid")
    print(f"   Key ID: {key['kid']}")
    print(f"   Algorithm: {key['alg']}")
    print(f"   Key type: {key['kty']}")
    return True

def main():
    print("\n" + "=" * 50)
    print("JWT TOKEN SIGNATURE TEST SUITE")
    print("=" * 50)

    tests = [
        test_jwks_format,
        test_keys_match,
        test_token_signature,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if all(results):
        print("\n✅ All tests passed! Token signature should work.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
