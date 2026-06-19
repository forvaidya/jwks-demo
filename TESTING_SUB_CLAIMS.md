# Testing Different Sub Claims

This guide shows how to test with different user IDs (sub claims) like `magic:mahesh`, `magic:john`, etc.

## Method 1: Using Environment Variables

```bash
# Test with magic:mahesh
export MAHESH_AWS_ROLE="123456789012:role/MyRole"
export AWS_USER_ID="magic:mahesh"
python3 aws_sts.py

# Test with magic:john
export AWS_USER_ID="magic:john"
python3 aws_sts.py

# Test with magic:alice
export AWS_USER_ID="magic:alice"
python3 aws_sts.py
```

## Method 2: Using Command-Line Arguments (Recommended)

```bash
# No need to set environment variables, pass them directly:

# Test magic:mahesh
python3 aws_sts.py --user-id magic:mahesh --role 123456789012:role/MyRole

# Test magic:john
python3 aws_sts.py --user-id magic:john --role 123456789012:role/MyRole

# Test magic:alice
python3 aws_sts.py --user-id magic:alice --role 123456789012:role/MyRole
```

### Available Options
```bash
python3 aws_sts.py --help

# Output:
# --user-id ID     Override AWS_USER_ID
# --role ARN       Override MAHESH_AWS_ROLE
# --issuer URL     Override issuer (default: http://localhost:3000)
```

## Method 3: Using Test Script (Test All at Once)

```bash
export MAHESH_AWS_ROLE="123456789012:role/MyRole"
python3 test_sub_claims.py
```

This tests all users at once and shows which ones succeeded/failed:

```
Testing Sub Claims (User IDs)
======================================================================

Role: 123456789012:role/MyRole
Test Users: magic:mahesh, magic:john, magic:alice

──────────────────────────────────────────────────────────────────────
Test 1/3: Sub Claim = 'magic:mahesh'
──────────────────────────────────────────────────────────────────────
✅ Success
   Role: 123456789012:role/MyRole
   User ID (sub): magic:mahesh
   Expiration: 2024-06-19T12:30:00+00:00

...

Results: 2/3 passed
```

## Method 4: Python API (Programmatic)

```python
from aws_sts import get_aws_credentials, set_aws_env_from_credentials
import os

# Test multiple users programmatically
test_users = [
    "magic:mahesh",
    "magic:john",
    "magic:alice",
]

role = "123456789012:role/MyRole"

for user_id in test_users:
    try:
        print(f"\nTesting: {user_id}")
        os.environ["MAHESH_AWS_ROLE"] = role
        os.environ["AWS_USER_ID"] = user_id
        
        creds = get_aws_credentials()
        print(f"✅ Success: {creds['Expiration']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
```

## AWS Configuration for Multiple Users

You need to configure AWS to accept these sub claims.

### Option A: Accept All Users with Pattern

In AWS IAM Role Trust Policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/localhost:3000"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "localhost:3000:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "localhost:3000:sub": "magic:*"
        }
      }
    }
  ]
}
```

This allows ANY sub claim matching the pattern `magic:*` (magic:mahesh, magic:john, magic:alice, etc.)

### Option B: Accept Specific Users Only

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/localhost:3000"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "localhost:3000:aud": "sts.amazonaws.com",
          "localhost:3000:sub": [
            "magic:mahesh",
            "magic:john",
            "magic:alice"
          ]
        }
      }
    }
  ]
}
```

This only allows the three specific users.

## Complete AWS Setup for Testing

### 1. Create OIDC Provider (One Time)

```bash
aws iam create-open-id-connect-provider \
  --url http://localhost:3000 \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "0000000000000000000000000000000000000000"
```

Output:
```
arn:aws:iam::123456789012:oidc-provider/localhost:3000
```

### 2. Create Role with Pattern-Based Trust Policy

```bash
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/localhost:3000"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "localhost:3000:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "localhost:3000:sub": "magic:*"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name TestRole \
  --assume-role-policy-document file://trust-policy.json
```

### 3. Attach Permissions to Role

```bash
# Attach a policy so the role can do something
aws iam attach-role-policy \
  --role-name TestRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess
```

### 4. Test All Users

```bash
export MAHESH_AWS_ROLE="123456789012:role/TestRole"

# Test each user
python3 aws_sts.py --user-id magic:mahesh
python3 aws_sts.py --user-id magic:john
python3 aws_sts.py --user-id magic:alice

# Or run all at once
python3 test_sub_claims.py
```

## Troubleshooting

### Error: "User is not authorized"

**Cause:** The `sub` claim doesn't match the trust policy condition.

**Fix:** Check AWS trust policy:
```bash
aws iam get-role-policy --role-name TestRole --policy-name TrustPolicy
```

The `localhost:3000:sub` condition must match your user ID format.

### Error: "InvalidIdentityToken"

**Cause:** OIDC provider URL or token format is wrong.

**Fix:**
1. Verify server is running: `python3 main.py`
2. Verify port is 3000
3. Check OIDC provider URL matches: `http://localhost:3000`

### Error: "OIDC provider not found"

**Cause:** OIDC provider wasn't created in AWS.

**Fix:**
```bash
aws iam create-open-id-connect-provider \
  --url http://localhost:3000 \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "0000000000000000000000000000000000000000"
```

## Quick Testing Checklist

- [ ] Server running: `python3 main.py` (port 3000)
- [ ] OIDC provider created in AWS IAM
- [ ] Role created with OIDC trust policy
- [ ] Trust policy includes sub claim condition
- [ ] Test with one user: `python3 aws_sts.py --user-id magic:mahesh --role 123456789012:role/TestRole`
- [ ] Run full test suite: `python3 test_sub_claims.py`

## JWT Token Contents

When you run:
```bash
python3 aws_sts.py --user-id magic:mahesh
```

The JWT token will contain:
```json
{
  "iss": "http://localhost:3000",
  "sub": "magic:mahesh",
  "aud": "sts.amazonaws.com",
  "iat": 1718873400,
  "exp": 1718877000
}
```

AWS will validate:
1. ✓ Signature using public key from `http://localhost:3000/.well-known/jwks.json`
2. ✓ Audience equals `sts.amazonaws.com`
3. ✓ Subject matches trust policy condition (e.g., `magic:*`)
4. ✓ Token not expired

If all checks pass → Credentials returned ✓
