import os
import json
import boto3
from datetime import datetime, timedelta
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import sys
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def load_private_key_from_file(key_path: str) -> str:
    """Load private key from file."""
    try:
        with open(key_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Private key not found at {key_path}. "
            "Start the FastAPI server first to generate keys."
        )


def create_oidc_jwt(
    private_key_pem: str,
    user_id: str,
    issuer: str = "http://localhost:3000",
    kid: str = "default"
) -> str:
    """
    Create a JWT token signed with the private key for OIDC authentication.

    Args:
        private_key_pem: Private key in PEM format
        user_id: User identifier (from AWS_USER_ID env var)
        issuer: OIDC issuer URL (the JWKS endpoint)
        kid: Key ID matching the one in JWKS

    Returns:
        Signed JWT token
    """
    now = datetime.utcnow()
    exp = now + timedelta(hours=1)

    payload = {
        "iss": issuer,
        "sub": user_id,
        "aud": "sts.amazonaws.com",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    token = jwt.encode(payload, private_key_pem, algorithm="RS256", headers={"kid": kid})
    return token


def assume_role_with_web_identity_oidc(
    role_arn: str,
    web_identity_token: str,
    duration_seconds: int = 3600,
    region: str = "ap-south-1",
    user_id: str = None
) -> dict:
    """
    Assume IAM role using OIDC federation with a valid JWT token.

    Args:
        role_arn: The ARN of the IAM role to assume
        web_identity_token: Signed JWT token for OIDC authentication
        duration_seconds: Token validity duration
        region: AWS region
        user_id: User identifier for session name

    Returns:
        Dictionary with AccessKeyId, SecretAccessKey, SessionToken, Expiration
    """
    sts_client = boto3.client("sts", region_name=region)

    # Sanitize session name (AWS allows only: alphanumeric, =, ., -, @, _)
    safe_user_id = (user_id or 'default').replace(":", "-").replace("*", "x")[:32]

    response = sts_client.assume_role_with_web_identity(
        RoleArn=role_arn,
        RoleSessionName=f"jwks-session-{safe_user_id}",
        WebIdentityToken=web_identity_token,
        DurationSeconds=duration_seconds
    )

    credentials = response["Credentials"]

    return {
        "AccessKeyId": credentials["AccessKeyId"],
        "SecretAccessKey": credentials["SecretAccessKey"],
        "SessionToken": credentials["SessionToken"],
        "Expiration": credentials["Expiration"].isoformat(),
    }


def get_aws_credentials(
    region: str = None,
    private_key_path: str = None,
    issuer: str = None
) -> dict:
    """
    Get AWS credentials using OIDC federation with JWKS.

    Constructs role ARN from environment variables:
    - AWS_ACCOUNT_ID: AWS account ID
    - MAHESH_AWS_ROLE: Role name (or full ARN)
    - AWS_USER_ID: User identifier

    Args:
        region: AWS region (default: from AWS_DEFAULT_REGION env var)
        private_key_path: Path to private key file (default: ./private_key.pem)
        issuer: OIDC issuer URL (default: from ISSUER env var)

    Returns:
        Dictionary with AWS credentials
    """
    # Get from env vars with defaults
    region = region or os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
    issuer = issuer or os.getenv("ISSUER", "http://localhost:3000")

    aws_account_id = os.getenv("AWS_ACCOUNT_ID")
    mahesh_aws_role = os.getenv("MAHESH_AWS_ROLE")
    aws_user_id = os.getenv("AWS_USER_ID")

    if not aws_account_id or not mahesh_aws_role or not aws_user_id:
        raise ValueError(
            "Environment variables required: AWS_ACCOUNT_ID, MAHESH_AWS_ROLE, AWS_USER_ID"
        )

    if private_key_path is None:
        private_key_path = os.path.join(os.path.dirname(__file__), "private_key.pem")

    private_key_pem = load_private_key_from_file(private_key_path)

    # Construct role ARN
    if mahesh_aws_role.startswith("arn:aws:iam::"):
        role_arn = mahesh_aws_role
    else:
        role_arn = f"arn:aws:iam::{aws_account_id}:role/{mahesh_aws_role}"

    if not role_arn.startswith("arn:aws:iam::"):
        raise ValueError(
            "Failed to construct valid role ARN"
        )

    web_identity_token = create_oidc_jwt(
        private_key_pem,
        aws_user_id,
        issuer=issuer
    )

    credentials = assume_role_with_web_identity_oidc(
        role_arn,
        web_identity_token,
        region=region,
        user_id=aws_user_id
    )

    return credentials


def set_aws_env_from_credentials(credentials: dict) -> None:
    """Set AWS environment variables from credentials dictionary."""
    os.environ["AWS_ACCESS_KEY_ID"] = credentials["AccessKeyId"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = credentials["SecretAccessKey"]
    os.environ["AWS_SESSION_TOKEN"] = credentials["SessionToken"]
    os.environ["AWS_DEFAULT_REGION"] = "ap-south-1"


def save_private_key(private_key_pem: str, key_path: str = None) -> str:
    """Save private key to file. Returns the path."""
    if key_path is None:
        key_path = os.path.join(os.path.dirname(__file__), "private_key.pem")

    os.makedirs(os.path.dirname(key_path) or ".", exist_ok=True)
    with open(key_path, 'w') as f:
        f.write(private_key_pem)
    os.chmod(key_path, 0o600)
    return key_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Get AWS credentials using OIDC federation"
    )
    parser.add_argument(
        "--role",
        help="IAM role ARN (overrides MAHESH_AWS_ROLE env var)",
        default=None
    )
    parser.add_argument(
        "--user-id",
        help="User ID for JWT sub claim (overrides AWS_USER_ID env var)",
        default=None
    )
    parser.add_argument(
        "--issuer",
        help="OIDC issuer URL (default: http://localhost:3000)",
        default="http://localhost:3000"
    )
    args = parser.parse_args()

    try:
        mahesh_aws_role = args.role or os.getenv("MAHESH_AWS_ROLE")
        aws_user_id = args.user_id or os.getenv("AWS_USER_ID")

        if not mahesh_aws_role or not aws_user_id:
            print("Usage:")
            print("  python3 aws_sts.py")
            print("    or")
            print("  python3 aws_sts.py --user-id magic:mahesh --role 123456789012:role/MyRole")
            print("\nEnvironment Variables:")
            print("  export MAHESH_AWS_ROLE='123456789012:role/MyRole'")
            print("  export AWS_USER_ID='magic:mahesh'")
            print("\nOptions:")
            print("  --user-id ID     Override AWS_USER_ID")
            print("  --role ARN       Override MAHESH_AWS_ROLE")
            print("  --issuer URL     Override issuer (default: http://localhost:3000)")
            sys.exit(1)

        print(f"\n📝 Using:")
        print(f"   Role: {mahesh_aws_role}")
        print(f"   User ID (sub): {aws_user_id}")
        print(f"   Issuer: {args.issuer}")

        credentials = get_aws_credentials(
            issuer=args.issuer
        )
        print("\n✅ Successfully obtained AWS credentials via OIDC")
        print(json.dumps({
            "AccessKeyId": credentials["AccessKeyId"][:20] + "...",
            "SecretAccessKey": "***REDACTED***",
            "SessionToken": "***REDACTED***",
            "Expiration": credentials["Expiration"]
        }, indent=2))

        set_aws_env_from_credentials(credentials)
        print("\n✅ AWS credentials set in environment variables")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
