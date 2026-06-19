# Multi-IDP Role Configuration

**Requirement:** Single IAM role trusts multiple OIDC Identity Providers (GitHub + Custom OIDC)

## Problem

- Have existing GitHub Actions OIDC role: `opera-github-actions-role`
- Need to add custom OIDC provider without creating new role
- Want same permissions for both IDPs

## Solution

Add multiple `Statement` blocks in role trust policy.

## Implementation

### Current State
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::521170656618:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:forvaidya/super-simple:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

### Add Custom OIDC Provider

Add new statement to same array:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GitHubOIDC",
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::521170656618:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:forvaidya/super-simple:ref:refs/heads/main"
        }
      }
    },
    {
      "Sid": "CustomOIDC",
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::521170656618:oidc-provider/oidc.awanipro.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.awanipro.com:aud": "sts.amazonaws.com",
          "oidc.awanipro.com:sub": [
            "magic:mahesh",
            "magic:john"
          ]
        }
      }
    }
  ]
}
```

## Usage

### GitHub Actions
```yaml
- name: Assume Role
  run: |
    # Uses GitHub's OIDC provider
    # Token validated against token.actions.githubusercontent.com
```

### Local/Custom
```bash
python3 aws_sts.py --user-id "magic:mahesh"
# Uses custom OIDC provider (oidc.awanipro.com)
# Token validated against that endpoint
```

## Key Points

✅ **Same role** - No duplication  
✅ **Different conditions** - Each IDP has own constraints  
✅ **Additive** - Add more IDPs by adding more statements  
✅ **Independent** - Each statement is evaluated separately  

## Update AWS Role

```bash
# Read current policy
aws iam get-role-policy --role-name opera-github-actions-role --policy-name TrustPolicy > current-policy.json

# Edit: Add CustomOIDC statement to Statement array

# Update
aws iam put-role-policy \
  --role-name opera-github-actions-role \
  --policy-name TrustPolicy \
  --policy-document file://current-policy.json
```

Or via console:
1. IAM → Roles → opera-github-actions-role
2. Trust relationships → Edit trust policy
3. Add second statement (CustomOIDC)
4. Update policy

## Verification

### Test GitHub OIDC
```bash
# GitHub Actions workflow uses this
echo "Tests GitHub provider"
```

### Test Custom OIDC
```bash
python3 aws_sts.py --user-id "magic:mahesh"
# ✅ Should get credentials if custom OIDC trust added
```

## Future: More IDPs

Add as many IDPs as needed - same role, multiple statements:

```json
"Statement": [
  { "Sid": "GitHubOIDC", ... },
  { "Sid": "CustomOIDC", ... },
  { "Sid": "AnotherProvider", ... },
  { "Sid": "YetAnotherProvider", ... }
]
```

Each with own Principal and Condition blocks.
