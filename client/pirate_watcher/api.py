import requests, os
from dotenv import load_dotenv
load_dotenv()
BACKEND_URL = os.getenv('BACKEND_URL','http://127.0.0.1:8000')
CLIENT_API_KEY = os.getenv('CLIENT_API_KEY','change-me-client')

def post_event(payload: dict):
    url = f"{BACKEND_URL}/api/v1/events"
    headers = {"X-API-Key": CLIENT_API_KEY}
    r = requests.post(url, json=payload, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()

def get_roster():
    url = f"{BACKEND_URL}/api/v1/roster"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json().get('roster', [])
    except Exception:
        return []
