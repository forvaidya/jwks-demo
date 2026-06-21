#!/bin/bash
# Print and decode the JWT token being sent to AWS

python3 << 'PYTHON'
import os
import sys
import json
import base64
from dotenv import load_dotenv
from aws_sts import create_oidc_jwt, load_private_key_from_file

load_dotenv()

# Get config
user_id = os.getenv('AWS_USER_ID', 'magic:mahesh')
issuer = os.getenv('ISSUER', 'https://oidc.awanipro.com')

try:
    # Load private key and create JWT
    private_key_pem = load_private_key_from_file('private_key.pem')
    token = create_oidc_jwt(private_key_pem, user_id, issuer=issuer)

    print("🔐 JWT Token:")
    print("=" * 80)
    print(token)
    print()

    # Decode header
    print("📋 JWT Header:")
    print("-" * 80)
    header = json.loads(base64.urlsafe_b64decode(token.split('.')[0] + '=='))
    print(json.dumps(header, indent=2))
    print()

    # Decode payload
    print("📋 JWT Payload (Claims):")
    print("-" * 80)
    payload = json.loads(base64.urlsafe_b64decode(token.split('.')[1] + '=='))
    print(json.dumps(payload, indent=2))
    print()

    # Signature info
    print("📋 JWT Signature:")
    print("-" * 80)
    signature = token.split('.')[2]
    print(f"Signature (first 50 chars): {signature[:50]}...")
    print()

    print("✅ This JWT will be sent to AWS STS AssumeRoleWithWebIdentity")
    print(f"   Issuer: {issuer}")
    print(f"   Subject: {user_id}")

except Exception as e:
    print(f"❌ Error: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON
