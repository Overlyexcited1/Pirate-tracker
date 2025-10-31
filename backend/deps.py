from fastapi import Header, HTTPException
import os
from dotenv import load_dotenv
load_dotenv()
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "change-me-admin")
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY", "change-me-client")
def require_client_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != CLIENT_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid client API key")
    return True
def require_admin_api_key(x_admin_key: str = Header(None)):
    if not x_admin_key or x_admin_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    return True
