#!/bin/bash
# Update AWS OIDC provider with current thumbprint

set -e

ISSUER="${ISSUER:-https://oidc.awanipro.com}"
ACCOUNT_ID="${AWS_ACCOUNT_ID:-521170656618}"

echo "🔄 Extracting thumbprint from JWKS..."

# Extract certificate from the server's TLS connection and get its thumbprint
THUMBPRINT=$(echo | openssl s_client -servername "${ISSUER#https://}" -connect "${ISSUER#https://}:443" 2>/dev/null | openssl x509 -fingerprint -noout | sed 's/SHA1 Fingerprint=//g' | sed 's/://g')

if [ -z "$THUMBPRINT" ]; then
  echo "❌ Failed to extract thumbprint"
  exit 1
fi

echo "✅ Thumbprint: $THUMBPRINT"
echo ""
echo "To update the OIDC provider, you can:"
echo ""
echo "1️⃣  Delete the old provider:"
echo "   aws iam delete-open-id-connect-provider --open-id-connect-provider-arn arn:aws:iam::$ACCOUNT_ID:oidc-provider/${ISSUER#https://}"
echo ""
echo "2️⃣  Create a new provider with the thumbprint:"
echo "   aws iam create-open-id-connect-provider \\"
echo "     --url $ISSUER \\"
echo "     --client-id-list sts.amazonaws.com \\"
echo "     --thumbprint-list $THUMBPRINT"
echo ""
echo "Or in AWS Console:"
echo "   IAM → Identity providers → Add provider"
echo "   Provider type: OpenID Connect"
echo "   Provider URL: $ISSUER"
echo "   Audience: sts.amazonaws.com"
echo "   Then paste thumbprint: $THUMBPRINT"
