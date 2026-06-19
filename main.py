from fastapi import FastAPI
from fastapi.responses import JSONResponse
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

@app.get("/.well-known/jwks.json")
async def get_jwks():
    return JSONResponse(content=jwks_cache)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
