#!/bin/bash
# Query the currently assumed role

echo "🔐 Assumed Role Information:"
echo "============================"

IDENTITY=$(aws sts get-caller-identity)
ROLE_ARN=$(echo "$IDENTITY" | grep -o 'arn:aws:iam::[^"]*')

echo "$IDENTITY" | jq .

echo ""
echo "Role ARN: $ROLE_ARN"

# Extract role name
ROLE_NAME=$(echo "$ROLE_ARN" | cut -d'/' -f2)
echo "Role Name: $ROLE_NAME"
