#!/usr/bin/env python3
"""
Client-side OIDC test: Get credentials and call AWS STS
"""

import os
import json
import sys
from aws_sts import get_aws_credentials, set_aws_env_from_credentials
import boto3

print("=" * 70)
print("Client-Side OIDC Test")
print("=" * 70)

# Get config from env
mahesh_aws_role = os.getenv("MAHESH_AWS_ROLE")
aws_user_id = os.getenv("AWS_USER_ID")

if not mahesh_aws_role or not aws_user_id:
    print("❌ Error: Set MAHESH_AWS_ROLE and AWS_USER_ID")
    sys.exit(1)

print(f"\n📝 Configuration:")
print(f"   Role: {mahesh_aws_role}")
print(f"   User: {aws_user_id}")

# Step 1: Get credentials via OIDC
print(f"\n1️⃣  Getting AWS credentials via OIDC...")
try:
    credentials = get_aws_credentials()
    print(f"✅ Credentials received")
    print(f"   AccessKeyId: {credentials['AccessKeyId'][:20]}...")
    print(f"   Expiration: {credentials['Expiration']}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n⚠️  Did you add the OIDC provider to AWS?")
    print("    1. IAM → Identity providers → Create provider")
    print("    2. URL: https://oidc.awanipro.com")
    print("    3. Audience: sts.amazonaws.com")
    print("    4. Get thumbprint (auto-fetch)")
    sys.exit(1)

# Step 2: Set environment variables
print(f"\n2️⃣  Setting AWS credentials in environment...")
set_aws_env_from_credentials(credentials)
print(f"✅ Environment variables set:")
print(f"   AWS_ACCESS_KEY_ID")
print(f"   AWS_SECRET_ACCESS_KEY")
print(f"   AWS_SESSION_TOKEN")
print(f"   AWS_DEFAULT_REGION: ap-south-1")

# Step 3: Call AWS STS GetCallerIdentity
print(f"\n3️⃣  Calling AWS STS GetCallerIdentity...")
try:
    sts_client = boto3.client("sts", region_name="ap-south-1")
    identity = sts_client.get_caller_identity()

    print(f"✅ Success!")
    print(f"\n📋 Caller Identity:")
    print(f"   Account: {identity['Account']}")
    print(f"   UserId: {identity['UserId']}")
    print(f"   Arn: {identity['Arn']}")

except Exception as e:
    print(f"❌ Error: {e}")
    print("\n⚠️  Possible issues:")
    print("    - OIDC provider not created in AWS")
    print("    - Role trust policy not configured")
    print("    - Wrong role ARN in MAHESH_AWS_ROLE")
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ OIDC Flow Complete!")
print("=" * 70)
print("\nYou can now use these credentials with AWS services:")
print("  - AWS CLI")
print("  - Boto3")
print("  - AWS SDKs")
print("\nCredentials are temporary (1 hour by default)")
print("=" * 70 + "\n")
