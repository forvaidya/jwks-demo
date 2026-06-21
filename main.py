from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from jwks_generator import generate_jwks, save_private_key, jwk_from_rsa_public_key, private_key_to_pem
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from dotenv import load_dotenv
import json
import os

# Load .env (searches current dir and parents - works with symlinks)
load_dotenv()

jwks_cache = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global jwks_cache
    private_key_path = os.path.join(os.path.dirname(__file__), "private_key.pem")

    # Check if private key already exists
    if os.path.exists(private_key_path):
        print(f"📂 Loading existing private key from {private_key_path}")
        with open(private_key_path, 'r') as f:
            private_key_pem = f.read()

        # Load the private key object to generate JWKS
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        jwk = jwk_from_rsa_public_key(public_key, "default")
        jwks_cache = {"keys": [jwk]}
        print(f"✅ Using existing keypair (thumbprint stable)")
    else:
        print(f"🔄 Generating new keypair...")
        jwks_cache, private_key_pem = generate_jwks()
        save_private_key(private_key_pem, private_key_path)
        print(f"✅ Keypair generated and private key saved to {private_key_path}")

    yield

app = FastAPI(lifespan=lifespan)

# Add CORS middleware for OIDC endpoints
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/.well-known/jwks.json")
async def get_jwks():
    return JSONResponse(content=jwks_cache)

@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    # Get issuer from ISSUER env var (loaded from .env)
    issuer = os.getenv("ISSUER", "https://oidc.awanipro.com")

    return JSONResponse(content={
        "issuer": issuer,
        "authorization_endpoint": f"{issuer}/auth",
        "token_endpoint": f"{issuer}/token",
        "jwks_uri": f"{issuer}/.well-known/jwks.json",
        "response_types_supported": ["id_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_methods_supported": ["none"]
    })

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
