# backend/routers/ops.py
from fastapi import APIRouter
from sqlalchemy import inspect, text
from backend.database import engine, Base
from backend import models  # ensure models are registered

router = APIRouter(prefix="/ops", tags=["ops"])

@router.get("/healthz")
def healthz():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.get("/dbz")
def dbz():
    insp = inspect(engine)
    return {"tables": insp.get_table_names()}

@router.post("/init-db")
def init_db():
    Base.metadata.create_all(bind=engine)
    insp = inspect(engine)
    return {"initialized": True, "tables": insp.get_table_names()}