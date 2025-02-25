from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
import requests
import os
import jwt
import time

from pydantic import BaseModel
import hashlib

SECRET = os.getenv("VP_SECRET") # Secret key for JWT encoding

# Helper function to hash passwords
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(login: str, password: str) -> bool:
    stored_hash = users.get(login)
    if not stored_hash:
        return False
    return stored_hash == password

def get_token():
    domain = 'http://xxxxxxxxxxxxxxxxxxxx.cloudapp.azure.com:8990'
    url = f'{domain}/realms/neone/protocol/openid-connect/token'
    basic = 'xxxxxxxxxxxxxxxxxxxxxxxx'
    
    headers = {
        'content-type': 'application/x-www-form-urlencoded',
        'authorization': f'Basic {basic}',
    }
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': 'neone-client'
    }
    
    response = requests.post(url, headers=headers, data=data)
    result = response.json()
    return result['access_token']

# Predefined users with hashed passwords
users = {
    "lucas":   hash_password("1234"),
    "alice":   hash_password("1234"),
    "bob":     hash_password("1234"),
    "charlie": hash_password("1234")
}

# Global token variable.
global_token = None

# Request model for authentication
class AuthRequest(BaseModel):
    login: str
    password: str

app = FastAPI()

# Endpoint for authentication
@app.post("/authenticate")
def authenticate(auth: AuthRequest):
    global global_token
    if check_credentials(auth.login, auth.password):
        global_token = get_token()
        return {
            "authenticated": True,
            "one_record_token": global_token
        }
    raise HTTPException(status_code=401, detail="Invalid login or password")

def issue_vp(did: str, claims: dict) -> str:
    # Create a mock VP token with basic claims and a short expiration
    vp = {
        "iss": did,
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,  # token valid for 10 minutes
        "vp": claims
    }
    token = jwt.encode(vp, SECRET, algorithm="HS256")
    return token

def verify_vp(token: str) -> dict:
    try:
        vp = jwt.decode(token, SECRET, algorithms=["HS256"])
        return vp
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid VP token")

@app.post("/issue-vp")
async def issue_vp_endpoint():
    # For the mock, we use a dummy decentralized identifier and example claims.
    did = "did:example:12345"
    claims = {"uld_id": "ULD123", "status": "ok", "owner": "AirlineA"}
    token = issue_vp(did, claims)
    return {"vp_token": token}

@app.post("/verify-vp")
async def verify_vp_endpoint(payload: dict):
    token = payload.get("vp_token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing vp_token")
    vp = verify_vp(token)
    return {"verified": True, "claims": vp}

