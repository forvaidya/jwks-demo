#!/usr/bin/env python3
"""
Example demonstrating JWKS server and AWS STS integration.

Prerequisites:
    1. Start the FastAPI server: python3 main.py
    2. Configure AWS OIDC provider (see README.md for setup)
    3. Set environment variables:
       export MAHESH_AWS_ROLE="123456789012:role/MyRole"
       export AWS_USER_ID="user@example.com"

Usage:
    python3 example_usage.py
"""

import os
import sys
import json
import requests
from jwks_generator import generate_jwks
from aws_sts import get_aws_credentials, set_aws_env_from_credentials


def example_1_generate_jwks():
    """Example 1: Generate and display JWKS."""
    print("\n=== Example 1: Generate JWKS (Local) ===\n")

    jwks, private_key_pem = generate_jwks(kid="example-key-1")
    print("Generated JWKS:")
    print(json.dumps(jwks, indent=2))

    print(f"\n✅ JWKS contains {len(jwks['keys'])} key(s)")
    print(f"✅ Private key generated (stored securely)")


def example_2_fetch_jwks_from_server():
    """Example 2: Fetch JWKS from running server."""
    print("\n=== Example 2: Fetch JWKS from Server ===\n")

    try:
        response = requests.get("http://localhost:3000/.well-known/jwks.json")
        if response.status_code == 200:
            jwks = response.json()
            print("✅ JWKS from server (http://localhost:3000/.well-known/jwks.json):")
            print(json.dumps(jwks, indent=2))
            return True
        else:
            print(f"❌ Failed to fetch JWKS: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server on localhost:3000")
        print("   Start the server with: python3 main.py")
        return False


def example_3_get_aws_credentials():
    """Example 3: Get AWS credentials via OIDC."""
    print("\n=== Example 3: Get AWS Credentials via OIDC ===\n")

    mahesh_aws_role = os.getenv("MAHESH_AWS_ROLE")
    aws_user_id = os.getenv("AWS_USER_ID")

    if not mahesh_aws_role or not aws_user_id:
        print("⚠️  Skipping AWS credentials example")
        print("Required environment variables not set:")
        print("  - MAHESH_AWS_ROLE=<account-id>:role/<role-name>")
        print("  - AWS_USER_ID=<user-identifier>")
        print("\nExample:")
        print("  export MAHESH_AWS_ROLE='123456789012:role/MyRole'")
        print("  export AWS_USER_ID='user@example.com'")
        return False

    try:
        print(f"Role ARN: arn:aws:iam::{mahesh_aws_role}")
        print(f"User ID: {aws_user_id}")
        print("\nAttempting to assume role using OIDC...")

        credentials = get_aws_credentials()

        print("\n✅ Successfully obtained AWS credentials via OIDC:")
        print(json.dumps(
            {
                "AccessKeyId": credentials["AccessKeyId"][:20] + "...",
                "SecretAccessKey": "***REDACTED***",
                "SessionToken": "***REDACTED***",
                "Expiration": credentials["Expiration"]
            },
            indent=2
        ))

        set_aws_env_from_credentials(credentials)
        print("\n✅ AWS credentials set in environment variables:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - AWS_SESSION_TOKEN")
        print("  - AWS_DEFAULT_REGION=ap-south-1")
        return True

    except Exception as e:
        print(f"❌ Error getting AWS credentials: {e}")
        return False


def example_4_test_health():
    """Example 4: Test server health."""
    print("\n=== Example 4: Test Server Health ===\n")

    try:
        response = requests.get("http://localhost:3000/health")
        if response.status_code == 200:
            health = response.json()
            print("✅ Server health check passed:")
            print(json.dumps(health, indent=2))
            return True
        else:
            print(f"❌ Health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server not running on localhost:3000")
        return False


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("JWKS Server and AWS STS Integration Examples")
    print("=" * 70)

    example_1_generate_jwks()
    server_running = example_2_fetch_jwks_from_server()
    aws_success = example_3_get_aws_credentials()
    example_4_test_health()

    print("\n" + "=" * 70)
    print("Examples Summary")
    print("=" * 70)
    print(f"Server running:         {'✅' if server_running else '❌'}")
    print(f"AWS credentials obtained: {'✅' if aws_success else '⚠️ (skipped)'}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
