# AWS OIDC Provider Setup

This guide explains how to set up and update the OIDC provider in AWS.

## Initial Setup (One-time)

### Via AWS Console (No AWS CLI needed) ✅ Recommended

1. Go to [AWS IAM → Identity providers](https://console.aws.amazon.com/iamv2/home#/identity_providers)
2. Click **"Add provider"**
3. Select **"OpenID Connect"**
4. Enter Provider URL: `https://oidc.awanipro.com`
5. Click **"Get thumbprint"** ← AWS automatically fetches the current thumbprint
6. Enter Audience (Client ID): `sts.amazonaws.com`
7. Click **"Add provider"**

Done! AWS automatically validates your JWKS endpoint and fetches the thumbprint.

## Update Thumbprint (if needed)

If your certificate/thumbprint changes, simply delete and recreate the provider using the same steps above. AWS will fetch the new thumbprint automatically.

## Via AWS CLI (Reference only)

If you have AWS CLI credentials and prefer command line:

```bash
bash docs/aws-cli-update-oidc.sh YOUR_THUMBPRINT
```

Example:
```bash
bash docs/aws-cli-update-oidc.sh 932bed339aa69212c89375b79304b475490b89a0
```

## Troubleshooting

**"Can't reach your identity provider"**
- Make sure Argo tunnel is running: `cloudflared tunnel run --url http://localhost:3000`
- Verify JWKS endpoint works: `curl https://oidc.awanipro.com/.well-known/jwks.json`

**Thumbprint mismatch**
- Delete the old provider in AWS Console
- Re-add it - AWS will fetch the current thumbprint automatically
- No manual thumbprint copying needed

## Key Points

- ✅ AWS Console automatically fetches thumbprint - easiest approach
- ✅ No AWS CLI credentials needed for setup
- ✅ One-time setup after OIDC provider is created
- ✅ Keypair is stable across server restarts (no more thumbprint changes)
