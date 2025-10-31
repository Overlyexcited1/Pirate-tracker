# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers as a package
from backend.routers import events, bounties, players, roster, heatmap

app = FastAPI(title="Pirate Bounty Tracker API", version="2.0")

# CORS (adjust origins later if you want)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(events.router)
app.include_router(bounties.router)
app.include_router(players.router)
app.include_router(roster.router)
app.include_router(heatmap.router)

@app.get("/healthz")
def healthz():
    return {"ok": True}