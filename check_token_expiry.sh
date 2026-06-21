#!/bin/bash
# Check AWS STS token expiration (in UTC)
# Portable across macOS, Linux, and other UNIX systems

if [ ! -f .aws_token_expiration.txt ]; then
  echo "❌ No token expiration found"
  echo "   Run: source <(bash get_aws_creds.sh | grep export)"
  exit 1
fi

EXPIRATION=$(cat .aws_token_expiration.txt)

# Use Python for portable date handling (works everywhere)
python3 << PYTHON
from datetime import datetime
import sys

try:
    # Parse the ISO format timestamp
    exp_str = "$EXPIRATION".replace('+00:00', '').replace('Z', '')
    expiration = datetime.fromisoformat(exp_str)
    current = datetime.utcnow()

    # Format readable string
    readable = expiration.strftime('%Y-%m-%d %H:%M:%S UTC')
    current_str = current.strftime('%Y-%m-%dT%H:%M:%S')

    print("🔐 Token Expiration (UTC):")
    print(f"   Expires: {readable}")
    print(f"   Current: {current_str}")

    # Check if expired and calculate remaining time
    if expiration > current:
        remaining = (expiration - current).total_seconds()
        minutes = int(remaining / 60)
        print(f"   ✅ Valid for {minutes} more minutes")
        sys.exit(0)
    else:
        print("   ❌ TOKEN EXPIRED")
        sys.exit(1)

except Exception as e:
    print(f"❌ Error parsing expiration: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON
