import os, requests

BASE = "https://api.starcitizen-api.com"
STARAPI_KEY = os.getenv("STARAPI_KEY", "")
STARAPI_MODE = os.getenv("STARAPI_MODE", "live")
STARAPI_TIMEOUT = float(os.getenv("STARAPI_TIMEOUT", "10"))

def _u(path: str) -> str:
    if not STARAPI_KEY:
        raise RuntimeError("STARAPI_KEY missing")
    return f"{BASE}/{STARAPI_KEY}/v1/{STARAPI_MODE}/{path.lstrip('/')}"

def fetch_user_org(handle: str) -> dict | None:
    """Return {'sid': '03B', 'name': 'Bulwark Bastion Brigade', 'rank': 'Member'} or None."""
    url = _u(f"user/{handle}")
    r = requests.get(url, timeout=STARAPI_TIMEOUT)
    if r.status_code != 200:
        return None
    data = r.json() or {}
    if data.get("success") != 1:
        return None
    org = (data.get("data") or {}).get("organization") or {}
    if not org:
        return None
    return {"sid": org.get("sid"), "name": org.get("name"), "rank": org.get("rank")}

def fetch_org_info(sid: str) -> dict | None:
    """Return org metadata to persist into organizations table."""
    url = _u(f"organization/{sid}")
    r = requests.get(url, timeout=STARAPI_TIMEOUT)
    if r.status_code != 200:
        return None
    data = r.json() or {}
    if data.get("success") != 1:
        return None
    org = data.get("data") or {}
    return {
        "sid": sid,
        "name": org.get("name"),
        "logo": (org.get("logo") or {}).get("source") if isinstance(org.get("logo"), dict) else org.get("logo"),
        "url":  org.get("site") or org.get("url"),
        "member_count": org.get("members") or org.get("member_count"),
    }
