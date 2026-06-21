#!/bin/bash
# Update AWS OIDC provider with new thumbprint (while keeping old ones)

set -e

ISSUER="${ISSUER:-https://oidc.awanipro.com}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-521170656618}"
NEW_THUMBPRINT="${1:-}"

if [ -z "$NEW_THUMBPRINT" ]; then
  echo "Usage: bash update_oidc_provider.sh <THUMBPRINT>"
  echo ""
  echo "Example:"
  echo "  bash update_oidc_provider.sh 932bed339aa69212c89375b79304b475490b89a0"
  exit 1
fi

PROVIDER_ARN="arn:aws:iam::$ACCOUNT_ID:oidc-provider/${ISSUER#https://}"

echo "🔄 Updating OIDC provider..."
echo "   Provider: ${ISSUER#https://}"
echo "   ARN: $PROVIDER_ARN"
echo "   New thumbprint: $NEW_THUMBPRINT"
echo ""

# Get current thumbprints
echo "📋 Fetching current provider configuration..."
CURRENT=$(aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$PROVIDER_ARN" 2>/dev/null || echo "{}")

if [ "$CURRENT" = "{}" ]; then
  echo "⚠️  Provider does not exist. Creating new provider..."
  aws iam create-open-id-connect-provider \
    --url "$ISSUER" \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list "$NEW_THUMBPRINT"
  echo "✅ Provider created with thumbprint: $NEW_THUMBPRINT"
else
  echo "✅ Provider exists, adding new thumbprint..."
  # Delete and recreate (AWS doesn't support updating thumbprints)
  aws iam delete-open-id-connect-provider \
    --open-id-connect-provider-arn "$PROVIDER_ARN"

  sleep 1

  aws iam create-open-id-connect-provider \
    --url "$ISSUER" \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list "$NEW_THUMBPRINT"

  echo "✅ Provider updated with new thumbprint: $NEW_THUMBPRINT"
fi

echo ""
echo "✅ Done! Test with: bash get_aws_creds.sh"
