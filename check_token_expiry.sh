#!/bin/bash
# Check AWS STS token expiration (in UTC)

if [ ! -f .aws_token_expiration.txt ]; then
  echo "❌ No token expiration found"
  echo "   Run: source <(bash get_aws_creds.sh | grep export)"
  exit 1
fi

EXPIRATION=$(cat .aws_token_expiration.txt)
CURRENT=$(date -u +%Y-%m-%dT%H:%M:%S)
READABLE=$(date -d "$EXPIRATION" -u '+%Y-%m-%d %H:%M:%S UTC')

echo "🔐 Token Expiration (UTC):"
echo "   Expires: $READABLE"
echo "   Current: $CURRENT"

# Check if expired
if [ "$EXPIRATION" \> "$CURRENT" ]; then
  REMAINING=$(( $(date -d "$EXPIRATION" +%s) - $(date +%s) ))
  MINUTES=$(( $REMAINING / 60 ))
  echo "   ✅ Valid for $MINUTES more minutes"
else
  echo "   ❌ TOKEN EXPIRED"
  exit 1
fi
