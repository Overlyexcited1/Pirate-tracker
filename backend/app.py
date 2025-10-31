# backend/app.py
from fastapi import FastAPI
from backend.database import Base, engine
from backend.routers import events, bounties, players, roster, heatmap

app = FastAPI(title="Pirate Bounty Tracker API", version="2.0")

# include routers
app.include_router(events.router)
app.include_router(bounties.router)
app.include_router(players.router)
app.include_router(roster.router)
app.include_router(heatmap.router)

# (optional) simple healthcheck
@app.get("/healthz")
def healthz():
    return {"ok": True}