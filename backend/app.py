# backend/app.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
import time
from sqlalchemy import text

from backend.database import Base, engine
from backend import models  # <-- import models BEFORE create_all so SQLAlchemy sees all tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    # wait briefly for DB to be ready
    for attempt in range(12):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            break
        except Exception as e:
            print(f"[startup] DB not ready (attempt {attempt+1}/12): {e}")
            time.sleep(5)

    print("[startup] creating tables …")
    try:
        Base.metadata.create_all(bind=engine)
        print("[startup] tables created")
    except Exception as e:
        print("[startup] create_all failed:", e)

    yield


app = FastAPI(title="Pirate Bounty Tracker API", version="2.0", lifespan=lifespan)

# Routers
from backend.routers import events, bounties, players, roster, heatmap, ops
app.include_router(events.router,   prefix="/api/v1")
app.include_router(bounties.router, prefix="/api/v1")
app.include_router(players.router,  prefix="/api/v1")
app.include_router(roster.router,   prefix="/api/v1")
app.include_router(heatmap.router,  prefix="/api/v1")
app.include_router(ops.router)  # health/debug