#!/bin/bash
# get_aws_creds.sh - Get AWS credentials and set environment variables

export MAHESH_AWS_ROLE="${MAHESH_AWS_ROLE:-123456789012:role/MyRole}"
export AWS_USER_ID="${AWS_USER_ID:-magic:mahesh}"
ISSUER="${ISSUER:-https://mytunnel-abc123.trycloudflare.com}"

# Run Python script and capture output
eval "$(python3 -c "
import os
import sys
import json
from aws_sts import get_aws_credentials, set_aws_env_from_credentials

try:
    # Get credentials
    creds = get_aws_credentials(issuer='$ISSUER')

    # Output as shell commands
    print(f'export AWS_ACCESS_KEY_ID=\"{creds[\"AccessKeyId\"]}\"')
    print(f'export AWS_SECRET_ACCESS_KEY=\"{creds[\"SecretAccessKey\"]}\"')
    print(f'export AWS_SESSION_TOKEN=\"{creds[\"SessionToken\"]}\"')
    print(f'export AWS_DEFAULT_REGION=\"ap-south-1\"')
    print(f'echo \"✅ AWS credentials set (expires: {creds[\"Expiration\"]})\"')
except Exception as e:
    print(f'echo \"❌ Error: {e}\"', file=sys.stderr)
    sys.exit(1)
")"
