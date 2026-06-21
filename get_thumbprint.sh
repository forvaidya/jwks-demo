#!/bin/bash
# Extract server certificate thumbprint (SHA-1 hash of X.509 certificate)
# As per AWS docs: "hex-encoded SHA-1 hash value of the X.509 certificate"

DOMAIN="${1:-oidc.awanipro.com}"
PORT="${2:-443}"

echo "🔐 Extracting SHA-1 thumbprint from certificate..."
echo "   Domain: $DOMAIN:$PORT"
echo ""

# Get certificate and calculate SHA-1 hash
THUMBPRINT=$(openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:$PORT" </dev/null 2>/dev/null | \
  openssl x509 -noout -fingerprint -sha1 2>/dev/null | \
  cut -d= -f2 | \
  tr -d ':')

if [ -z "$THUMBPRINT" ]; then
  echo "❌ Failed to extract thumbprint"
  echo "   Make sure the domain is reachable: $DOMAIN:$PORT"
  exit 1
fi

echo "✅ Server certificate thumbprint (SHA-1):"
echo "   $THUMBPRINT"
echo ""
echo "Use this in AWS OIDC Provider:"
echo "   1. IAM → Identity providers"
echo "   2. Add provider → OpenID Connect"
echo "   3. Provider URL: https://$DOMAIN"
echo "   4. Thumbprint: $THUMBPRINT"
