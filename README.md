# JWKS Server with AWS STS Integration

A FastAPI server that serves JSON Web Key Sets (JWKS) and integrates with AWS STS for passwordless credential acquisition via OIDC federation.

## Features

- **JWKS Generation**: Auto-generates RSA keypair on each server startup
- **JWKS Endpoint**: Serves keys at `/.well-known/jwks.json` (RFC 7517 compliant)
- **AWS STS Integration**: Passwordless credential retrieval using OIDC federation
- **Environment-based Configuration**: Uses `MAHESH_AWS_ROLE` and `AWS_USER_ID` environment variables

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

Server runs on `http://localhost:3000`

**Endpoints:**
- `GET /.well-known/jwks.json` - Returns JWKS with RSA public key
- `GET /health` - Health check

**Example:**
```bash
curl http://localhost:3000/.well-known/jwks.json | jq .
```

### Generating JWKS

Standalone JWKS generation:
```bash
source venv/bin/activate
python3 jwks_generator.py
```

### AWS STS Integration

**Prerequisites:**
1. Start the FastAPI server: `python3 main.py` (generates and saves private key)
2. Configure AWS OIDC provider (see "AWS IAM Setup" below)

Get AWS credentials using OIDC federation:

```bash
export MAHESH_AWS_ROLE="123456789012:role/MyRole"
export AWS_USER_ID="user@example.com"

source venv/bin/activate
python3 aws_sts.py
```

**Environment Variables Required:**
- `MAHESH_AWS_ROLE`: ARN in format `<account-id>:role/<role-name>`
- `AWS_USER_ID`: User identifier for the OIDC token
- `AWS_DEFAULT_REGION`: Defaults to `ap-south-1` if not set

**Output:**
```json
{
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "SessionToken": "...",
  "Expiration": "2024-06-19T10:30:00+00:00"
}
```

**How it works:**
1. `aws_sts.py` loads the private key saved by the server (`./private_key.pem`)
2. Creates a JWT token signed with the private key
3. Calls AWS STS `AssumeRoleWithWebIdentity` with the JWT
4. Returns temporary credentials

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
