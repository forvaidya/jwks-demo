# AWS STS OIDC Integration Guide

This guide walks through setting up passwordless AWS credential acquisition using OIDC federation.

## Quick Start

### 1. Start the JWKS Server

```bash
source venv/bin/activate
python3 main.py
```

The server will:
- Generate a new RSA keypair
- Save the private key to `./private_key.pem` (chmod 600)
- Serve the public key at `http://localhost:3000/.well-known/jwks.json`

### 2. Configure AWS OIDC Provider

#### Via AWS CLI

```bash
aws iam create-open-id-connect-provider \
  --url http://localhost:3000 \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "$(curl -s http://localhost:3000/.well-known/jwks.json | python3 -c 'import sys, json; print(json.load(sys.stdin)["keys"][0].get("x5t", "0" * 40))')"
```

#### Via AWS Console

1. Go to **IAM → Identity providers → Create provider**
2. Select **OpenID Connect**
3. Provider URL: `http://localhost:3000`
4. Client ID: `sts.amazonaws.com`
5. Click **Get thumbprint** (fetches from your JWKS endpoint)
6. Click **Create**

### 3. Create IAM Role with OIDC Trust

Create a role with this trust policy:

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

### 4. Get AWS Credentials

```bash
export MAHESH_AWS_ROLE="123456789012:role/MyRole"
export AWS_USER_ID="user@example.com"

python3 aws_sts.py
```

Output:
```json
{
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "SessionToken": "...",
  "Expiration": "2024-06-19T12:00:00+00:00"
}
```

## Using with Argo Tunnel

### 1. Expose via Argo Tunnel

Terminal 1 (FastAPI server):
```bash
source venv/bin/activate
python3 main.py
```

Terminal 2 (Argo Tunnel):
```bash
cloudflared tunnel run --url http://localhost:3000
```

Copy the tunnel URL: `https://YOUR-RANDOM-DOMAIN.trycloudflare.com`

### 2. Update AWS OIDC Provider

```bash
TUNNEL_URL="https://YOUR-RANDOM-DOMAIN.trycloudflare.com"

aws iam create-open-id-connect-provider \
  --url $TUNNEL_URL \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list "0000000000000000000000000000000000000000"
```

Note: AWS will validate the thumbprint when you use the provider.

### 3. Update Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/YOUR-RANDOM-DOMAIN.trycloudflare.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "YOUR-RANDOM-DOMAIN.trycloudflare.com:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

### 4. Use the Tunnel Domain in Environment Variable

```bash
export MAHESH_AWS_ROLE="123456789012:role/MyRole"
export AWS_USER_ID="user@example.com"

# Create a modified aws_sts.py call that uses the tunnel URL
# Or update the issuer parameter if calling from Python
python3 -c "
import os
from aws_sts import get_aws_credentials, set_aws_env_from_credentials

creds = get_aws_credentials(
    issuer='https://YOUR-RANDOM-DOMAIN.trycloudflare.com'
)
set_aws_env_from_credentials(creds)
print('✅ Credentials obtained via Argo Tunnel!')
"
```

## Environment Variables

| Variable | Format | Example | Required |
|----------|--------|---------|----------|
| `MAHESH_AWS_ROLE` | `<account>:role/<name>` | `123456789012:role/MyRole` | Yes |
| `AWS_USER_ID` | User identifier | `user@example.com` | Yes |
| `AWS_DEFAULT_REGION` | AWS region | `ap-south-1` | No |

## Token Lifecycle

- **JWT Token Lifetime**: 1 hour (configurable)
- **AWS Session Token Lifetime**: Based on role max duration (default 1 hour)
- **Tokens Refresh**: Run `aws_sts.py` again to get new credentials

## Troubleshooting

### "Private key not found"
- Make sure the server is running: `python3 main.py`
- Check that `./private_key.pem` exists in the project directory

### "InvalidIdentityToken" from AWS
- JWT token may be expired (> 1 hour old)
- OIDC issuer URL doesn't match in trust policy
- Run `aws_sts.py` again to generate a fresh token

### "User: arn:aws:iam::... is not authorized to perform: sts:AssumeRoleWithWebIdentity"
- Role doesn't have OIDC trust relationship set up
- Verify trust policy is correctly configured
- Check that audience (`aud`) in trust policy matches `sts.amazonaws.com`

### Thumbprint validation fails
- Get fresh thumbprint: `curl http://localhost:3000/.well-known/jwks.json`
- Update OIDC provider with new thumbprint
- Or delete and recreate the OIDC provider

## RFC Compliance

- **RFC 7515**: JSON Web Signature (JWS)
- **RFC 7517**: JSON Web Key (JWK)
- **RFC 7518**: JSON Web Algorithms (JWA) - RS256
- **RFC 7519**: JSON Web Token (JWT)

## Security Considerations

- Private key is stored in `./private_key.pem` with permissions 600 (read-only by owner)
- Private key is regenerated on each server restart
- JWT tokens have 1-hour expiration
- No credentials are saved to disk (only in memory)
- Session tokens are provided by AWS STS (temporary, time-limited)
- Requires valid AWS IAM configuration for exploitation prevention

## References

- [AWS OIDC Provider Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for_idp_oidc.html)
- [AssumeRoleWithWebIdentity API](https://docs.aws.amazon.com/STS/latest/APIReference/API_AssumeRoleWithWebIdentity.html)
- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [Cloudflare Argo Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
