# Argo Tunnel + Magic Sub Claims Setup

Quick reference for setting up your custom OIDC with Argo Tunnel using `magic:` prefix.

## Side-by-Side Comparison

### GitHub Actions OIDC
```json
{
  "Effect": "Allow",
  "Principal": {
    "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
  },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
      "token.actions.githubusercontent.com:sub": "repo:forvaidya/super-simple:ref:refs/heads/main"
    }
  }
}
```

### Your Custom Magic OIDC (Argo Tunnel)
```json
{
  "Effect": "Allow",
  "Principal": {
    "Federated": "arn:aws:iam::123456789012:oidc-provider/mytunnel-abc123.trycloudflare.com"
  },
  "Action": "sts:AssumeRoleWithWebIdentity",
  "Condition": {
    "StringEquals": {
      "mytunnel-abc123.trycloudflare.com:aud": "sts.amazonaws.com",
      "mytunnel-abc123.trycloudflare.com:sub": "magic:mahesh"
    }
  }
}
```

## Complete Setup

### 1. Start Server (Locally)
```bash
source venv/bin/activate
python3 main.py
# Server running on http://localhost:3000
```

### 2. Start Argo Tunnel
```bash
cloudflared tunnel run --url http://localhost:3000
# https://mytunnel-abc123.trycloudflare.com
```

### 3. Create AWS OIDC Provider
```bash
aws iam create-open-id-connect-provider \
  --url https://mytunnel-abc123.trycloudflare.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "0000000000000000000000000000000000000000"
```

### 4. Create IAM Role with Trust Policy

**Single User (magic:mahesh):**
```bash
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/mytunnel-abc123.trycloudflare.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "mytunnel-abc123.trycloudflare.com:aud": "sts.amazonaws.com",
          "mytunnel-abc123.trycloudflare.com:sub": "magic:mahesh"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name MyMagicRole \
  --assume-role-policy-document file://trust-policy.json
```

**Multiple Users (magic:*):**
```bash
cat > trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/mytunnel-abc123.trycloudflare.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "mytunnel-abc123.trycloudflare.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "mytunnel-abc123.trycloudflare.com:sub": "magic:*"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name MyMagicRole \
  --assume-role-policy-document file://trust-policy.json
```

### 5. Test Credentials

```bash
export MAHESH_AWS_ROLE="123456789012:role/MyMagicRole"

# Test magic:mahesh
python3 aws_sts.py \
  --user-id "magic:mahesh" \
  --issuer "https://mytunnel-abc123.trycloudflare.com"

# Test magic:john
python3 aws_sts.py \
  --user-id "magic:john" \
  --issuer "https://mytunnel-abc123.trycloudflare.com"

# Test magic:alice
python3 aws_sts.py \
  --user-id "magic:alice" \
  --issuer "https://mytunnel-abc123.trycloudflare.com"
```

## Format Reference

| Component | GitHub | Your Magic OIDC |
|-----------|--------|-----------------|
| **Issuer** | `token.actions.githubusercontent.com` | `mytunnel-abc123.trycloudflare.com` |
| **OIDC Provider ARN** | `arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com` | `arn:aws:iam::123456789012:oidc-provider/mytunnel-abc123.trycloudflare.com` |
| **Audience Claim** | `token.actions.githubusercontent.com:aud` | `mytunnel-abc123.trycloudflare.com:aud` |
| **Subject Claim** | `token.actions.githubusercontent.com:sub` | `mytunnel-abc123.trycloudflare.com:sub` |
| **Subject Value** | `repo:forvaidya/super-simple:ref:refs/heads/main` | `magic:mahesh` |
| **Subject Pattern** | `repo:forvaidya/*` | `magic:*` |

## Key Differences

### ✅ What's the Same
- Both use OpenID Connect (OIDC)
- Both follow the same AWS IAM trust policy structure
- Both use JWT tokens with `iss`, `sub`, `aud` claims
- Both validate signatures against a JWKS endpoint

### ✅ What's Different
| Aspect | GitHub | Your OIDC |
|--------|--------|----------|
| **Hosted By** | GitHub (official) | You (Argo Tunnel) |
| **Subject Format** | Structured (repo semantics) | Custom (magic: prefix) |
| **Issuer Domain** | `token.actions.githubusercontent.com` | Your tunnel domain |
| **JWKS Endpoint** | GitHub's endpoint | Your server |
| **Key Rotation** | GitHub manages | You manage |

## JWT Token Example

When you run:
```bash
python3 aws_sts.py --user-id "magic:mahesh" --issuer "https://mytunnel-abc123.trycloudflare.com"
```

JWT contains:
```json
{
  "iss": "https://mytunnel-abc123.trycloudflare.com",
  "sub": "magic:mahesh",
  "aud": "sts.amazonaws.com",
  "iat": 1718873400,
  "exp": 1718877000
}
```

AWS validates:
1. ✓ Fetches public key from `https://mytunnel-abc123.trycloudflare.com/.well-known/jwks.json`
2. ✓ Verifies JWT signature
3. ✓ Checks `aud` == `sts.amazonaws.com`
4. ✓ Checks `sub` matches trust policy: `magic:mahesh`
5. ✓ Checks token not expired
6. ✓ Returns credentials

## Troubleshooting

### Error: "OIDC provider not found"
- OIDC provider not created in AWS
- Check: `aws iam list-open-id-connect-providers`

### Error: "User is not authorized"
- Trust policy `sub` doesn't match
- Update trust policy with correct user ID

### Error: "InvalidIdentityToken"
- JWT signature verification failed
- Check: Argo Tunnel is running
- Verify: AWS can reach `https://mytunnel-abc123.trycloudflare.com/.well-known/jwks.json`

### Error: "Connection refused"
- Server not running
- Start: `python3 main.py`

## Using with Your Applications

### AWS CLI
```bash
# After getting credentials
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

aws s3 ls
```

### Python/Boto3
```python
from aws_sts import get_aws_credentials, set_aws_env_from_credentials

creds = get_aws_credentials(issuer="https://mytunnel-abc123.trycloudflare.com")
set_aws_env_from_credentials(creds)

# Now use boto3
import boto3
s3 = boto3.client('s3')
s3.list_buckets()
```

### GitHub Actions (Future)
```yaml
- name: Get AWS Credentials
  run: |
    python3 aws_sts.py \
      --user-id "magic:mahesh" \
      --issuer "https://mytunnel-abc123.trycloudflare.com"
```
