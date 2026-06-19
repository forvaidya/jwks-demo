# JWKS Server with AWS STS Integration

A complete **OIDC Provider** built with FastAPI that enables passwordless AWS credential federation.

## What You Can Do With This

This is an **OpenID Connect (OIDC) authentication system** that lets you:

- **Get AWS credentials without AWS SSO login** - Sign a JWT with your private key → AWS validates signature → Get temp credentials
- **Authenticate apps/services with custom identities** - Use `magic:mahesh`, `magic:john`, or any custom `sub` claim

- **Enable passwordless to AWS ** - from your laptop

- **Implement cross-account federation** - External systems trust your OIDC provider and get temporary AWS roles

## Key Capabilities

| Capability | Description |
|-----------|-------------|
| **OIDC Provider** | Generates and serves JWKS with RS256-signed JWT tokens |
| **AWS STS Integration** | Calls `AssumeRoleWithWebIdentity` with signed JWT to get temp credentials |
| **Custom Sub Claims** | Support any identity pattern: `magic:mahesh`, `user@company.com`, `app-name`, etc. |
| **Zero Credentials** | No passwords, no stored keys — only temporary signed tokens |
| **IAM Trust Policies** | AWS validates JWT signature and enforces role access via sub claim |
| **Argo Tunnel Ready** | Expose publicly at any domain (e.g., `https://oidc.awanipro.com`) |

## Features

- **OIDC Provider**: Auto-generates RSA keypair on startup, serves JWKS and OpenID Configuration
- **JWT Signing**: Creates RS256-signed tokens with custom `sub` claims
- **AWS STS Integration**: Exchanges JWT for temporary AWS credentials
- **No Passwords**: Entirely passwordless authentication via OIDC federation
- **Environment-based Configuration**: Uses `MAHESH_AWS_ROLE`, `AWS_USER_ID`, `ISSUER` env vars
- **Multi-Identity Support**: Allow multiple users/services via IAM trust policy conditions

## Project Structure

```
.
├── main.py                 # FastAPI server
├── jwks_generator.py       # JWKS generation logic
├── aws_sts.py              # AWS STS OIDC integration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the JWKS Server

```bash
source venv/bin/activate
python3 main.py
```

Server runs on `http://localhost:3000` (or via Argo Tunnel at your configured domain)

**Endpoints:**
- `GET /.well-known/jwks.json` - Returns JWKS with RSA public key (RFC 7517 compliant)
- `GET /.well-known/openid-configuration` - Returns OIDC metadata
- `GET /health` - Health check

**Verify the server:**
```bash
curl http://localhost:3000/.well-known/jwks.json | jq .
curl http://localhost:3000/.well-known/openid-configuration | jq .
```

### Getting AWS Credentials via OIDC

**Prerequisites:**
1. Start the FastAPI server: `python3 main.py` (generates and saves private key)
2. Set up AWS OIDC provider and IAM role (see "AWS IAM Setup" below)
3. Configure environment variables

**Step 1: Set environment variables**
```bash
export MAHESH_AWS_ROLE="123456789012:role/MyRole"  # or full ARN
export AWS_USER_ID="magic:mahesh"                   # or any identifier
export ISSUER="http://localhost:3000"               # or your Argo Tunnel URL
export AWS_DEFAULT_REGION="ap-south-1"
```

**Step 2: Get credentials**
```bash
source venv/bin/activate
python3 aws_sts.py
```

**Output:**
```json
{
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "SessionToken": "...",
  "Expiration": "2024-06-19T10:30:00+00:00"
}
```

**How it works (OIDC flow):**
1. Server generates RS256-signed JWT with claims: `iss`, `sub`, `aud`, `iat`, `exp`
2. Client loads private key from `./private_key.pem`
3. Client signs JWT and sends to AWS STS `AssumeRoleWithWebIdentity`
4. AWS fetches JWKS from `/.well-known/jwks.json` endpoint
5. AWS verifies JWT signature against public key
6. AWS checks `sub` claim against IAM role trust policy
7. AWS returns temporary credentials (AccessKeyId, SecretAccessKey, SessionToken)

## Testing & Integration Guide

### Local Testing (Passwordless Authentication)

This proves the system works **without AWS SSO login** — truly passwordless.

**Step 1: Start the JWKS server**
```bash
source venv/bin/activate
python3 main.py
```

Server generates keypair on startup and saves private key to `./private_key.pem`.

**Step 2: Configure environment**
```bash
# Copy .env.example to .env first if needed
# cat .env.example > .env

# Edit .env with your values
export AWS_ACCOUNT_ID="52XXXXXXXX"
export MAHESH_AWS_ROLE="opera-github-actions-role"
export AWS_USER_ID="magic:mahesh"
export ISSUER="http://localhost:3000"
export AWS_DEFAULT_REGION="ap-south-1"
```

**Step 3: Test OIDC credential retrieval**
```bash
source venv/bin/activate

# Log out of AWS SSO first (proves it's truly passwordless)
aws sso logout

# Get OIDC credentials
python3 aws_sts.py
```

**Step 4: Export credentials for use**
```bash
# Export in shell format (single line per credential, no line breaks)
source venv/bin/activate
python3 get_creds_export.py

# Output:
# export AWS_ACCESS_KEY_ID=ASIA...
# export AWS_SECRET_ACCESS_KEY=...
# export AWS_SESSION_TOKEN=...
# export AWS_DEFAULT_REGION=ap-south-1
```

**Step 5: Test AWS CLI operations**
```bash
# Copy the export lines and paste into your shell, then:
aws sts get-caller-identity

# Should output:
# {
#     "UserId": "AROAXSWBRDVVFVA4BXFVU:jwks-session-magic-mahesh",
#     "Account": "52XXXXXXXX",
#     "Arn": "arn:aws:sts::52XXXXXXXX:assumed-role/opera-github-actions-role/jwks-session-magic-mahesh"
# }
```

**Step 6: Test S3 access**
```bash
# Using OIDC credentials:
aws s3 ls

# Should list all S3 buckets (if role has S3 permissions)
```

**Verification Checklist:**
- ✅ Keypair regenerates on each server restart
- ✅ JWT tokens are RS256-signed
- ✅ AWS STS validates JWT against JWKS endpoint
- ✅ Credentials work **without AWS SSO login**
- ✅ Credentials are temporary (1 hour by default)
- ✅ S3 operations succeed with OIDC credentials

---

### Generic OIDC Integration Guide

This system can integrate with **any OIDC provider** that AWS trusts. Here's how to adapt it:

#### 1. Understand the Key Concepts

| Concept | Meaning | Example |
|---------|---------|---------|
| **Issuer** | The OIDC provider URL | `http://localhost:3000` or `https://oidc.awanipro.com` |
| **Audience** | Who the token is for | `sts.amazonaws.com` (always this for AWS) |
| **Subject (sub)** | The user/identity claim | `magic:mahesh` or `user@company.com` |
| **JWKS URI** | Public keys endpoint | `{issuer}/.well-known/jwks.json` |
| **OpenID Config** | OIDC metadata | `{issuer}/.well-known/openid-configuration` |

#### 2. Customize for Your OIDC Provider

**Option A: Using This Code (FastAPI-based)**

If you're building your own OIDC provider using this code:

```python
# In main.py, set your issuer
export ISSUER="https://your-domain.com"

# In aws_sts.py, customize the sub claim
# Default uses AWS_USER_ID env var, modify as needed
```

**Option B: Pointing to External OIDC Provider**

If using an existing OIDC provider (e.g., Auth0, Okta, GitHub Actions):

```python
# In aws_sts.py, change the issuer and get token from provider
issuer = "https://external-provider.com"  # Not localhost:3000
web_identity_token = get_token_from_external_provider()  # Custom logic
```

#### 3. AWS IAM Role Configuration for Any OIDC

**For your custom OIDC provider:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/your-issuer.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "your-issuer.com:aud": "sts.amazonaws.com",
          "your-issuer.com:sub": "your-subject-claim"
        }
      }
    }
  ]
}
```

Replace:
- `ACCOUNT_ID` → Your AWS account ID
- `your-issuer.com` → Your OIDC issuer domain
- `your-subject-claim` → Expected value of the `sub` claim in JWT

**Examples:**

For GitHub Actions OIDC:
```json
"Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com",
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
  },
  "StringLike": {
    "token.actions.githubusercontent.com:sub": "repo:owner/repo:ref:refs/heads/main"
  }
}
```

For Google Cloud (external account federation):
```json
"Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/accounts.google.com",
"Condition": {
  "StringEquals": {
    "accounts.google.com:aud": "sts.amazonaws.com"
  }
}
```

#### 4. Test Your Integration

```bash
# 1. Start your OIDC provider
python3 main.py  # or run your external provider

# 2. Verify JWKS endpoint
curl https://your-issuer.com/.well-known/jwks.json | jq .

# 3. Get token from your provider
TOKEN=$(your-method-to-get-jwt)

# 4. Test AWS STS
aws sts assume-role-with-web-identity \
  --role-arn arn:aws:iam::ACCOUNT_ID:role/RoleName \
  --role-session-name test-session \
  --web-identity-token $TOKEN

# 5. Use credentials
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
aws sts get-caller-identity
```

#### 5. Common OIDC Patterns

**Pattern 1: User-based (Email/Username)**
```
sub: "user@company.com"
# Trust anyone from your domain
"StringLike": { "issuer:sub": "*@company.com" }
```

**Pattern 2: Service-based (App ID)**
```
sub: "app-name"
# Trust specific applications
"StringEquals": { "issuer:sub": "app-name" }
```

**Pattern 3: Repository-based (CI/CD)**
```
sub: "repo:owner/name:environment:prod"
# Trust specific repos or environments
"StringLike": { "issuer:sub": "repo:myorg/*:environment:*" }
```

**Pattern 4: Magic Prefix (Custom)**
```
sub: "magic:mahesh" or "magic:john"
# Trust multiple users via wildcard
"StringLike": { "issuer:sub": "magic:*" }
```

---

## Architecture

### JWKS Generation & Storage
1. Server starts → Generates new RSA keypair (2048-bit)
2. Public key formatted as JWK and served at `/.well-known/jwks.json`
3. Private key saved to `./private_key.pem` (chmod 600) for AWS STS script to use
4. On each server restart, both keys are regenerated

### AWS STS OIDC Flow
1. AWS client loads private key from `./private_key.pem`
2. Creates JWT with claims: `iss`, `sub`, `aud`, `iat`, `exp`
3. Signs JWT with RS256 using the private key
4. Calls AWS STS `AssumeRoleWithWebIdentity` with signed JWT
5. AWS validates JWT signature against JWKS endpoint
6. Receives temporary AWS credentials (AccessKeyId, SecretAccessKey, SessionToken)

## Security Notes

- New keypair generated on **each server restart**
- No credentials stored on disk
- JWT tokens expire in 1 hour by default
- AWS session tokens are temporary (STS controlled)
- Requires valid AWS IAM trust relationship with OIDC provider

## AWS IAM Setup

### Step 1: Create OIDC Provider

1. Go to IAM → Identity providers
2. Create provider:
   - **Provider type**: OpenID Connect
   - **Provider URL**: `http://localhost:3000` (or your Argo Tunnel URL)
   - **Audience**: `sts.amazonaws.com`
3. Click "Get thumbprint" (will fetch from JWKS endpoint)
4. Create provider

### Step 2: Create IAM Role with OIDC Trust

Create or update a role with this trust relationship policy:

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
          "localhost:3000:sub": "user@example.com"
        }
      }
    }
  ]
}
```

Replace:
- `123456789012` with your AWS account ID
- `localhost:3000` with your Argo Tunnel domain when using tunneling
- `user@example.com` with expected user IDs (or remove the `sub` condition)

### Step 2b: Example with Argo Tunnel + Custom Magic Format

When using **Argo Tunnel** with custom `magic:` prefix sub claims:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.awanipro.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.awanipro.com:aud": "sts.amazonaws.com",
          "oidc.awanipro.com:sub": "magic:mahesh"
        }
      }
    }
  ]
}
```

Or accept multiple magic users with wildcard:

```json
{
  "Condition": {
    "StringEquals": {
      "oidc.awanipro.com:aud": "sts.amazonaws.com"
    },
    "StringLike": {
      "oidc.awanipro.com:sub": "magic:*"
    }
  }
}
```

**For reference, here's how GitHub Actions compares:**

```json
{
  "Condition": {
    "StringEquals": {
      "oidc.awanipro.com:aud": "sts.amazonaws.com",
      "oidc.awanipro.com:sub": "repo:forvaidya/super-simple:ref:refs/heads/main"
    }
  }
}
```

Replace `oidc.awanipro.com` with your actual Argo Tunnel domain.

### Step 3: Attach Permissions

Attach a permissions policy to the role (e.g., for S3 access):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "*"
    }
  ]
}
```

## RFC Compliance

- **RFC 7517**: JSON Web Key (JWK) - Key format
- **RFC 7515**: JSON Web Signature (JWS) - Token signing
- **RFC 7518**: JSON Web Algorithms (JWA) - RS256
- **RFC 7519**: JSON Web Token (JWT) - Token structure

## Argo Tunnel Setup

To expose the server publicly via Argo Tunnel:

### 1. Start the FastAPI server
```bash
python3 main.py
```

### 2. In another terminal, run Argo Tunnel
```bash
cloudflared tunnel run --url http://localhost:3000
```

Output will show:
```
2024-06-19T10:00:00Z INF +----------------------------+
2024-06-19T10:00:00Z INF |   Your quick Tunnel has been created!  Visit it:   |
2024-06-19T10:00:00Z INF |   https://oidc.awanipro.com   |
2024-06-19T10:00:00Z INF +----------------------------+
```

### 3. Test the tunnel
```bash
curl https://oidc.awanipro.com/.well-known/jwks.json
```

### 4. Update AWS OIDC Provider
- Use the Argo Tunnel URL instead of `localhost:3000`
- Update provider URL to: `https://oidc.awanipro.com`
- Regenerate thumbprint

### 5. Update Environment Variables
```bash
export MAHESH_AWS_ROLE="123456789012:role/MyRole"
export AWS_USER_ID="user@example.com"
python3 aws_sts.py
```

The script will:
- Load the private key from `./private_key.pem`
- Create a JWT signed with your private key
- Call AWS with the correct issuer URL
- Return temporary credentials
