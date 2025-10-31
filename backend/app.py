from database import Base, engine

# create tables once on boot
Base.metadata.create_all(bind=engine)

from routers import events, bounties, players, roster, heatmap

app = FastAPI(title="Pirate Bounty Tracker API", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(events.router, prefix="/api/v1")
app.include_router(bounties.router, prefix="/api/v1")
app.include_router(players.router, prefix="/api/v1")
app.include_router(roster.router, prefix="/api/v1")
app.include_router(heatmap.router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"ok": True}
