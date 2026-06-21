#!/bin/bash
# Verify AWS credentials by testing STS and S3 access

set -e

echo "🔐 Verifying AWS Credentials..."
echo ""

# Check if credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
  echo "❌ Error: AWS_ACCESS_KEY_ID not set"
  echo "   First run: source <(bash get_aws_creds.sh)"
  exit 1
fi

echo "📋 Credentials loaded"
echo "   Region: $AWS_DEFAULT_REGION"
echo ""

# Test 1: STS GetCallerIdentity
echo "🔍 Test 1: STS GetCallerIdentity"
echo "   Calling: aws sts get-caller-identity"
STS_RESULT=$(aws sts get-caller-identity 2>&1)

if [ $? -eq 0 ]; then
  echo "   ✅ Success!"
  echo "$STS_RESULT" | python3 -m json.tool | sed 's/^/      /'
else
  echo "   ❌ Failed!"
  echo "$STS_RESULT" | sed 's/^/      /'
  exit 1
fi

echo ""

# Test 2: S3 List Buckets
echo "🔍 Test 2: S3 List Buckets"
echo "   Calling: aws s3 ls"
S3_RESULT=$(aws s3 ls 2>&1)

if [ $? -eq 0 ]; then
  echo "   ✅ Success!"
  if [ -z "$S3_RESULT" ]; then
    echo "      (No S3 buckets found)"
  else
    echo "$S3_RESULT" | sed 's/^/      /'
  fi
else
  echo "   ❌ Failed!"
  echo "$S3_RESULT" | sed 's/^/      /'
  echo "   (This is normal if the role doesn't have S3 permissions)"
fi

echo ""
echo "✅ Credential verification complete!"
