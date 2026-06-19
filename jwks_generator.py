import json
import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from typing import Dict, Any, Tuple


def int_to_base64url(val: int, length: int) -> str:
    """Convert integer to base64url encoded string."""
    bytes_val = val.to_bytes(length, byteorder='big')
    return base64.urlsafe_b64encode(bytes_val).rstrip(b'=').decode('ascii')


def generate_rsa_keypair() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Generate RSA keypair for JWKS."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key


def private_key_to_pem(private_key: rsa.RSAPrivateKey) -> str:
    """Convert private key to PEM format."""
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')


def jwk_from_rsa_public_key(public_key: rsa.RSAPublicKey, kid: str) -> Dict[str, Any]:
    """Convert RSA public key to JWK format (RFC 7517)."""
    public_numbers = public_key.public_numbers()

    n = int_to_base64url(public_numbers.n, (public_numbers.n.bit_length() + 7) // 8)
    e = int_to_base64url(public_numbers.e, (public_numbers.e.bit_length() + 7) // 8)

    return {
        "kty": "RSA",
        "use": "sig",
        "kid": kid,
        "n": n,
        "e": e,
        "alg": "RS256"
    }


def generate_jwks(kid: str = "default") -> Tuple[Dict[str, Any], str]:
    """
    Generate complete JWKS with a single RSA keypair.

    Returns:
        Tuple of (jwks_dict, private_key_pem)
    """
    private_key, public_key = generate_rsa_keypair()
    jwk = jwk_from_rsa_public_key(public_key, kid)
    private_key_pem = private_key_to_pem(private_key)

    jwks = {
        "keys": [jwk]
    }

    return jwks, private_key_pem


def save_private_key(private_key_pem: str, key_path: str = None) -> str:
    """Save private key to file. Returns the path."""
    if key_path is None:
        key_path = os.path.join(os.path.dirname(__file__), "private_key.pem")

    os.makedirs(os.path.dirname(key_path) or ".", exist_ok=True)
    with open(key_path, 'w') as f:
        f.write(private_key_pem)
    os.chmod(key_path, 0o600)
    return key_path


def get_jwks_json(kid: str = "default") -> str:
    """Generate JWKS and return as JSON string."""
    jwks, _ = generate_jwks(kid)
    return json.dumps(jwks, indent=2)


if __name__ == "__main__":
    print(get_jwks_json())
