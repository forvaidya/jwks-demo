#!/usr/bin/env python3
"""Output AWS credentials in export format"""

import os
import sys
from aws_sts import get_aws_credentials

creds = get_aws_credentials()

# Output on single lines (no wrapping)
sys.stdout.write(f"export AWS_ACCESS_KEY_ID={creds['AccessKeyId']}\n")
sys.stdout.write(f"export AWS_SECRET_ACCESS_KEY={creds['SecretAccessKey']}\n")
sys.stdout.write(f"export AWS_SESSION_TOKEN={creds['SessionToken']}\n")
sys.stdout.write(f"export AWS_DEFAULT_REGION=ap-south-1\n")
sys.stdout.flush()
