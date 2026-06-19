# Structured Sub Claims (GitHub OIDC Style)

Your GitHub OIDC uses structured sub claims like:
```
repo:forvaidya/super-simple:ref:refs/heads/main
```

You can use the same pattern for your local OIDC setup!

## Examples

### GitHub Style Repo Format
```
repo:forvaidya/super-simple:ref:refs/heads/main
repo:forvaidya/super-simple:ref:refs/heads/develop
repo:forvaidya/super-simple:environment:production
```

### Service/Environment Format
```
service:api-server:env:production
service:api-server:env:staging
service:worker:env:production
service:frontend:region:ap-south-1
```

### Application Format
```
app:my-app:user:mahesh
app:my-app:user:john
app:my-app:deployment:eu-west-1
```

## AWS Configuration

### Pattern 1: GitHub Repo Reference

```bash
# Test
python3 aws_sts.py \
  --user-id "repo:forvaidya/super-simple:ref:refs/heads/main" \
  --role 123456789012:role/MyRole
```

AWS Trust Policy:
```json
{
  "Condition": {
    "StringLike": {
      "localhost:3000:sub": "repo:forvaidya/super-simple:ref:*"
    }
  }
}
```

### Pattern 2: Service + Environment

```bash
# Test production
python3 aws_sts.py \
  --user-id "service:api-server:env:production" \
  --role 123456789012:role/MyRole

# Test staging
python3 aws_sts.py \
  --user-id "service:api-server:env:staging" \
  --role 123456789012:role/MyRole
```

AWS Trust Policy:
```json
{
  "Condition": {
    "StringLike": {
      "localhost:3000:sub": "service:api-server:env:*"
    }
  }
}
```

### Pattern 3: GitHub Actions (Exact Match)

If you want to use the exact GitHub format:

```json
{
  "Condition": {
    "StringEquals": {
      "localhost:3000:sub": "repo:forvaidya/super-simple:ref:refs/heads/main"
    }
  }
}
```

Test:
```bash
python3 aws_sts.py \
  --user-id "repo:forvaidya/super-simple:ref:refs/heads/main" \
  --role 123456789012:role/MyRole
```

## Complete AWS Setup Example

### 1. Create OIDC Provider

```bash
aws iam create-open-id-connect-provider \
  --url http://localhost:3000 \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "0000000000000000000000000000000000000000"
```

### 2. Create Role with Structured Sub Claims

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
          "localhost:3000:sub": "repo:forvaidya/*"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name GitHubActionsRole \
  --assume-role-policy-document file://trust-policy.json
```

### 3. Test Different Branches

```bash
export MAHESH_AWS_ROLE="123456789012:role/GitHubActionsRole"

# Main branch
python3 aws_sts.py --user-id "repo:forvaidya/super-simple:ref:refs/heads/main"

# Develop branch
python3 aws_sts.py --user-id "repo:forvaidya/super-simple:ref:refs/heads/develop"

# Feature branch
python3 aws_sts.py --user-id "repo:forvaidya/super-simple:ref:refs/heads/feature/new-feature"
```

## Test Script for Structured Claims

Create `test_structured_sub_claims.py`:

```python
#!/usr/bin/env python3

import os
import sys
import subprocess

# Define your test cases with structured sub claims
TEST_CASES = [
    {
        "name": "Main Branch",
        "sub": "repo:forvaidya/super-simple:ref:refs/heads/main"
    },
    {
        "name": "Develop Branch",
        "sub": "repo:forvaidya/super-simple:ref:refs/heads/develop"
    },
    {
        "name": "Feature Branch",
        "sub": "repo:forvaidya/super-simple:ref:refs/heads/feature/auth"
    },
    {
        "name": "Production Service",
        "sub": "service:api-server:env:production"
    },
    {
        "name": "Staging Service",
        "sub": "service:api-server:env:staging"
    },
]

MAHESH_AWS_ROLE = os.getenv("MAHESH_AWS_ROLE")
if not MAHESH_AWS_ROLE:
    print("❌ MAHESH_AWS_ROLE not set")
    sys.exit(1)

print("=" * 70)
print("Testing Structured Sub Claims")
print("=" * 70)

for i, test in enumerate(TEST_CASES, 1):
    print(f"\n{i}. {test['name']}")
    print(f"   Sub: {test['sub']}")
    
    result = subprocess.run(
        [
            sys.executable,
            "aws_sts.py",
            "--user-id", test['sub'],
            "--role", MAHESH_AWS_ROLE,
        ],
        capture_output=True,
        text=True,
    )
    
    if result.returncode == 0:
        print("   ✅ Success")
    else:
        print("   ❌ Failed")
        if "not authorized" in result.stderr:
            print("      (Check AWS trust policy conditions)")
```

Run:
```bash
export MAHESH_AWS_ROLE="123456789012:role/GitHubActionsRole"
python3 test_structured_sub_claims.py
```

## AWS Trust Policy Wildcards

| Pattern | Matches |
|---------|---------|
| `repo:forvaidya/*` | Any repo by forvaidya |
| `repo:forvaidya/super-simple:ref:*` | Any branch in super-simple |
| `repo:forvaidya/super-simple:ref:refs/heads/*` | Any branch (not tags) |
| `repo:forvaidya/super-simple:environment:*` | Any environment |
| `service:*:env:production` | Any service in production |
| `*:api-server:env:*` | api-server in any environment |

## Real-World Example: GitHub Actions

### Scenario
Your GitHub Actions workflow in `forvaidya/super-simple` needs AWS credentials.

### Local Setup

**1. Trust Policy:**
```json
{
  "Condition": {
    "StringEquals": {
      "localhost:3000:aud": "sts.amazonaws.com"
    },
    "StringLike": {
      "localhost:3000:sub": "repo:forvaidya/super-simple:*"
    }
  }
}
```

**2. Test locally:**
```bash
export MAHESH_AWS_ROLE="123456789012:role/GitHubActionsRole"

# Simulate GitHub Actions
python3 aws_sts.py \
  --user-id "repo:forvaidya/super-simple:ref:refs/heads/main" \
  --issuer http://localhost:3000
```

**3. Later with Argo Tunnel:**
```bash
cloudflared tunnel run --url http://localhost:3000
# Now your GitHub Actions can use: https://YOUR-TUNNEL-DOMAIN
```

## JWT Payload Example

When you run:
```bash
python3 aws_sts.py --user-id "repo:forvaidya/super-simple:ref:refs/heads/main"
```

JWT contains:
```json
{
  "iss": "http://localhost:3000",
  "sub": "repo:forvaidya/super-simple:ref:refs/heads/main",
  "aud": "sts.amazonaws.com",
  "iat": 1718873400,
  "exp": 1718877000
}
```

AWS validates:
- ✓ `sub` matches trust policy pattern
- ✓ `aud` == `sts.amazonaws.com`
- ✓ Token signature valid
- ✓ Token not expired

## Comparison with GitHub

| Component | GitHub OIDC | Your Local OIDC |
|-----------|-------------|-----------------|
| Issuer | `https://token.actions.githubusercontent.com` | `http://localhost:3000` |
| Sub Format | `repo:owner/repo:ref:refs/heads/branch` | Same! Or custom format |
| Audience | `123456789012` (account ID) | `sts.amazonaws.com` |
| Trust Policy | AWS IAM | AWS IAM |

You can use the exact GitHub format or create your own structured format!
