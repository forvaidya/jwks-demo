from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from jwks_generator import generate_jwks, save_private_key
import json
import os

jwks_cache = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global jwks_cache
    jwks_cache, private_key_pem = generate_jwks()

    # Save private key for AWS STS script to use
    private_key_path = os.path.join(os.path.dirname(__file__), "private_key.pem")
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
    issuer = os.getenv("ISSUER", "http://localhost:3000")
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
