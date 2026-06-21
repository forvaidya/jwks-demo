#!/bin/bash
# get_aws_creds.sh - Get AWS credentials via OIDC federation
#
# USAGE:
#   source <(bash get_aws_creds.sh | grep export)
#
# Or with grep to filter exports only:
#   source <(bash get_aws_creds.sh | grep "^export ")
#
# Then verify credentials:
#   aws sts get-caller-identity
#   aws s3 ls
#
# WHAT IT DOES:
#   1. Restarts FastAPI server (reuses existing keypair for stable thumbprint)
#   2. Loads private key from file
#   3. Creates JWT signed with private key
#   4. Calls AWS STS AssumeRoleWithWebIdentity
#   5. Outputs export statements for AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, etc.
#
# ENVIRONMENT:
#   Load from .env or set manually:
#   - AWS_ACCOUNT_ID: Your AWS account ID
#   - MAHESH_AWS_ROLE: IAM role name or ARN
#   - AWS_USER_ID: Subject claim for JWT (e.g., magic:mahesh)
#   - ISSUER: OIDC issuer URL (e.g., https://oidc.awanipro.com)

# Kill any existing FastAPI server process and restart
echo "🔄 Restarting FastAPI server..." >&2
# Kill by port to be more reliable
lsof -ti:3000 | xargs -r kill -9 2>/dev/null
sleep 1
# NOTE: NOT deleting private_key.pem - we keep the same keypair for stable thumbprint

# Start fresh FastAPI server
sleep 1
python main.py > /tmp/jwks_server.log 2>&1 &
SERVER_PID=$!

# Wait for server to be ready and private key generated (max 10 seconds)
for i in {1..20}; do
  if curl -s http://localhost:3000/health >/dev/null 2>&1 && [ -f private_key.pem ]; then
    echo "✅ FastAPI server ready (PID: $SERVER_PID)" >&2
    break
  fi
  if [ $i -eq 20 ]; then
    echo "❌ Error: FastAPI server failed to start or generate keys" >&2
    cat /tmp/jwks_server.log >&2
    exit 1
  fi
  sleep 0.5
done

# Load from .env file if present
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Use env vars or defaults
export MAHESH_AWS_ROLE="${MAHESH_AWS_ROLE:-opera-github-actions-role}"
export AWS_USER_ID="${AWS_USER_ID:-magic:mahesh}"
export AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-521170656618}"
ISSUER="${ISSUER:-https://oidc.awanipro.com}"

# Run Python script and capture output + save expiration to file
CREDS_SCRIPT="$(python3 -c "
import os
import sys
import json
from aws_sts import get_aws_credentials, set_aws_env_from_credentials

try:
    # Get credentials
    creds = get_aws_credentials(issuer='$ISSUER')

    # Save expiration to file for later checking
    with open('.aws_token_expiration.txt', 'w') as f:
        f.write(creds['Expiration'])

    # Output as shell commands
    print(f'export AWS_ACCESS_KEY_ID=\"{creds[\"AccessKeyId\"]}\"')
    print(f'export AWS_SECRET_ACCESS_KEY=\"{creds[\"SecretAccessKey\"]}\"')
    print(f'export AWS_SESSION_TOKEN=\"{creds[\"SessionToken\"]}\"')
    print(f'export AWS_DEFAULT_REGION=\"ap-south-1\"')
    print(f'export TOKEN_EXPIRATION=\"{creds[\"Expiration\"]}\"')
    print(f'echo \"✅ Fresh Token Generated\"')
    print(f'echo \"   Expires (UTC): {creds[\"Expiration\"]}\"')
except Exception as e:
    print(f'echo \"❌ Error: {e}\"', file=sys.stderr)
    sys.exit(1)
")"

# Output only the exports (everything else goes to stderr)
echo "$CREDS_SCRIPT" | grep export > aws-temp-creds.rc
echo "$CREDS_SCRIPT" | grep echo

# Parse and display expiration date
EXPIRATION=$(grep TOKEN_EXPIRATION aws-temp-creds.rc | cut -d'"' -f2)
READABLE_DATE=$(date -d "$EXPIRATION" '+%A, %B %d at %I:%M %p' 2>/dev/null || echo "$EXPIRATION")

cat << EOF

✅ Token Expiration: $READABLE_DATE

To load credentials:
  source aws-temp-creds.rc

Verify with STS:
  aws sts get-caller-identity

EOF