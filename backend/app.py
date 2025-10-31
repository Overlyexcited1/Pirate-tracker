# backend/app.py
from fastapi import FastAPI
from backend.database import Base, engine
from backend.routers import events, bounties, players, roster, heatmap

app = FastAPI(title="Pirate Bounty Tracker API", version="2.0")

# include routers
app.include_router(events.router,   prefix="/api/v1")
app.include_router(bounties.router, prefix="/api/v1")
app.include_router(players.router,  prefix="/api/v1")
app.include_router(roster.router,   prefix="/api/v1")
app.include_router(heatmap.router,  prefix="/api/v1")

# (optional) simple healthcheck
@app.get("/healthz")
def healthz():
    return {"ok": True}