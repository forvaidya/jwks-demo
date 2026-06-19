#!/usr/bin/env python3
"""
Test script to verify different sub claim values work with AWS OIDC.

This script tests getting credentials with different user IDs (sub claims).

Usage:
    python3 test_sub_claims.py
"""

import os
import sys
import json
import subprocess
from datetime import datetime

# Test users with different sub claim formats
TEST_USERS = [
    "magic:mahesh",
    "magic:john",
    "magic:alice",
]

# You need to set this environment variable
MAHESH_AWS_ROLE = os.getenv("MAHESH_AWS_ROLE")
if not MAHESH_AWS_ROLE:
    print("❌ Error: MAHESH_AWS_ROLE environment variable not set")
    print("\nExample:")
    print("  export MAHESH_AWS_ROLE='123456789012:role/MyRole'")
    print("  python3 test_sub_claims.py")
    sys.exit(1)

print("=" * 70)
print("Testing Sub Claims (User IDs)")
print("=" * 70)
print(f"\nRole: {MAHESH_AWS_ROLE}")
print(f"Test Users: {', '.join(TEST_USERS)}\n")

results = []

for i, user_id in enumerate(TEST_USERS, 1):
    print(f"\n{'─' * 70}")
    print(f"Test {i}/{len(TEST_USERS)}: Sub Claim = '{user_id}'")
    print(f"{'─' * 70}")

    try:
        # Call aws_sts.py with command-line arguments
        result = subprocess.run(
            [
                sys.executable,
                "aws_sts.py",
                "--user-id", user_id,
                "--role", MAHESH_AWS_ROLE,
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            print(f"✅ Success")
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'Expiration' in line or 'AccessKeyId' in line or 'Using:' in line:
                    print(f"   {line}")
            results.append({
                "user_id": user_id,
                "status": "✅ SUCCESS",
                "output": result.stdout
            })
        else:
            print(f"❌ Failed")
            print(f"   Error: {result.stderr[:100]}")
            results.append({
                "user_id": user_id,
                "status": "❌ FAILED",
                "error": result.stderr
            })

    except subprocess.TimeoutExpired:
        print(f"❌ Timeout")
        results.append({
            "user_id": user_id,
            "status": "⏱️  TIMEOUT",
            "error": "Request timed out"
        })
    except Exception as e:
        print(f"❌ Error: {e}")
        results.append({
            "user_id": user_id,
            "status": "❌ ERROR",
            "error": str(e)
        })

# Summary
print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)

for result in results:
    print(f"{result['user_id']:20} → {result['status']}")

# AWS Configuration Reminder
print("\n" + "=" * 70)
print("AWS Configuration Required")
print("=" * 70)
print("\nMake sure your AWS IAM role trust policy includes conditions for")
print("each sub claim you want to allow. Example:\n")

print("""
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/localhost:3000"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "localhost:3000:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "localhost:3000:sub": "magic:*"
        }
      }
    }
  ]
}
""")

print("This trust policy allows ANY sub claim matching 'magic:*' pattern")
print("Or be more specific with individual users:")

print("""
"StringEquals": {
  "localhost:3000:sub": "magic:mahesh"
}
""")

passed = sum(1 for r in results if "SUCCESS" in r['status'])
total = len(results)

print(f"\n{'=' * 70}")
print(f"Results: {passed}/{total} passed")
print(f"{'=' * 70}\n")

sys.exit(0 if passed == total else 1)
