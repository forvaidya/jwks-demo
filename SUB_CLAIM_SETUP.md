# JWT `sub` Claim Configuration for AWS

## What is the `sub` Claim?

The `sub` (subject) claim in a JWT token identifies the user or entity making the request. It's set to the value of your `AWS_USER_ID` environment variable.

## How It's Generated

In `aws_sts.py`, the JWT token is created with:

```python
payload = {
    "iss": "http://localhost:3000",  # Issuer
    "sub": user_id,                  # <- This is your AWS_USER_ID
    "aud": "sts.amazonaws.com",      # Audience
    "iat": int(now.timestamp()),     # Issued at
    "exp": int(exp.timestamp()),     # Expires
}
```

## Environment Variable

```bash
export AWS_USER_ID="mahesh@example.com"  # This becomes the "sub" claim
```

When you run `python3 aws_sts.py`, the JWT will contain:
```json
{
  "sub": "mahesh@example.com"
}
```

## AWS Configuration

You configure how AWS validates the `sub` claim in the **IAM Role Trust Policy**.

### Option 1: Accept Any `sub` (Permissive)

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
        }
      }
    }
  ]
}
```

In this case, any `sub` value is accepted.

### Option 2: Restrict to Specific `sub` Values (Recommended)

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
          "localhost:3000:sub": "mahesh@example.com"
        }
      }
    }
  ]
}
```

Replace `"mahesh@example.com"` with your actual `AWS_USER_ID`.

### Option 3: Restrict to Pattern (Wildcard)

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
          "localhost:3000:sub": "mahesh*"
        }
      }
    }
  ]
}
```

This accepts any `sub` starting with "mahesh".

## Port Information

The server runs on **port 3000**:

```
http://localhost:3000/.well-known/jwks.json
```

In AWS trust policy, use:
```json
"localhost:3000:aud": "sts.amazonaws.com",
"localhost:3000:sub": "YOUR_USER_ID"
```

## Complete Setup Example

### 1. Set Environment Variables
```bash
export MAHESH_AWS_ROLE="123456789012:role/MyRole"
export AWS_USER_ID="mahesh@example.com"
```

### 2. Start Server
```bash
python3 main.py
# Server running on http://localhost:3000
```

### 3. Create AWS OIDC Provider

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

### 4. Create IAM Role with Trust Policy

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
          "localhost:3000:aud": "sts.amazonaws.com",
          "localhost:3000:sub": "mahesh@example.com"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name MyRole \
  --assume-role-policy-document file://trust-policy.json
```

### 5. Get Credentials

```bash
python3 aws_sts.py
```

## Token Flow Diagram

```
User's Script
    |
    ├─ Reads: AWS_USER_ID="mahesh@example.com"
    |
    ├─ Creates JWT payload with:
    |  ├─ "sub": "mahesh@example.com"
    |  ├─ "iss": "http://localhost:3000"
    |  └─ "aud": "sts.amazonaws.com"
    |
    ├─ Signs with private key (RS256)
    |
    └─ Sends to AWS STS
          |
          └─ AWS validates:
             ├─ Signature (using public key from JWKS)
             ├─ Audience == "sts.amazonaws.com"
             └─ Subject == "mahesh@example.com" ✓
                
          └─ Returns temporary credentials ✓
```

## Troubleshooting

**Error: "User is not authorized to perform: sts:AssumeRoleWithWebIdentity"**

→ Check that the `sub` in trust policy matches your `AWS_USER_ID`

```bash
# In your terminal:
echo $AWS_USER_ID

# Should match "sub" value in AWS trust policy
```

**Error: "InvalidIdentityToken"**

→ The token structure is wrong. Make sure:
- Server is running on port 3000
- `AWS_USER_ID` is set correctly
- OIDC provider URL matches `http://localhost:3000`

**Error: "NoSuchEntity"**

→ OIDC provider might not exist. Create it:

```bash
aws iam create-open-id-connect-provider \
  --url http://localhost:3000 \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

## Quick Reference

| Component | Value | Notes |
|-----------|-------|-------|
| Port | 3000 | Server port |
| Issuer (`iss`) | http://localhost:3000 | In JWT |
| Audience (`aud`) | sts.amazonaws.com | In JWT and trust policy |
| Subject (`sub`) | $AWS_USER_ID | In JWT and trust policy |
| Algorithm | RS256 | JWT signing method |
| Key Size | 2048-bit RSA | Cryptography standard |
