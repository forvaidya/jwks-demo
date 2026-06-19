#!/usr/bin/env python3
"""
Output AWS credentials as shell export commands.

Usage:
    eval "$(python3 creds_export.py)"

    or

    source <(python3 creds_export.py)
"""

import os
import sys
import json
from aws_sts import get_aws_credentials

def main():
    """Get credentials and output as shell exports."""

    # Get config from environment
    role = os.getenv("MAHESH_AWS_ROLE")
    user_id = os.getenv("AWS_USER_ID")
    issuer = os.getenv("ISSUER", "https://oidc.awanipro.com")

    if not role or not user_id:
        print(
            "echo '❌ Error: Set MAHESH_AWS_ROLE and AWS_USER_ID'",
            file=sys.stderr
        )
        sys.exit(1)

    try:
        # Get credentials
        creds = get_aws_credentials(issuer=issuer)

        # Output as shell export commands
        print(f'export AWS_ACCESS_KEY_ID="{creds["AccessKeyId"]}"')
        print(f'export AWS_SECRET_ACCESS_KEY="{creds["SecretAccessKey"]}"')
        print(f'export AWS_SESSION_TOKEN="{creds["SessionToken"]}"')
        print(f'export AWS_DEFAULT_REGION="ap-south-1"')
        print(f'echo "✅ AWS credentials loaded (expires: {creds["Expiration"]}"')

    except Exception as e:
        print(f'echo "❌ Error: {e}"', file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
