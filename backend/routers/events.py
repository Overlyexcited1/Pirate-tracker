# backend/routers/events.py

from fastapi import APIRouter, Depends, HTTPException, Path, BackgroundTasks
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import Event
from schemas import EventCreate, EventOut
from deps import require_client_api_key, require_admin_api_key
import crud

# starcitizen-api.com enrichment
from tasks import enrich_attacker_org

# If you rely on SQLAlchemy to create tables at boot, keep this:
Base.metadata.create_all(bind=engine)

# NOTE: your app likely applies the /api/v1 prefix when including this router in app.py.
# If you prefer it local to this file instead, change to: APIRouter(prefix="/api/v1", tags=["events"])
router = APIRouter(tags=["events"])


@router.post("/events", response_model=EventOut, dependencies=[Depends(require_client_api_key)])
def post_event(
    payload: EventCreate,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Create an event, link attacker/victim Players, update stats,
    then (if attacker_org is missing) kick off background enrichment to
    fetch org info from starcitizen-api.com and upsert into `organizations`.
    """
    # Upsert players
    attacker = crud.get_or_create_player(
        db, payload.attacker_id, payload.attacker_name, org=payload.attacker_org
    )
    victim = crud.get_or_create_player(
        db, payload.victim_id, payload.victim_name
    )

    # Persist event via your existing CRUD (keeps your mapping/validation)
    ev = crud.create_event(db, payload)

    # Link relationships and commit once
    ev.attacker = attacker
    ev.victim = victim
    db.commit()

    # Update aggregate stats with your existing helper
    crud.update_player_stats(db, attacker, victim, ev)
    db.commit()

    # Background enrichment ONLY if org missing/empty and we have a handle
    try:
        if not (payload.attacker_org and payload.attacker_org.strip()) and payload.attacker_name:
            # Pass attacker handle; player_id optional (use getattr in case None)
            bg.add_task(enrich_attacker_org, payload.attacker_name, getattr(attacker, "player_id", None))
    except Exception as e:
        # best-effort; don't fail the request if scheduling fails
        print("enrich_attacker_org schedule failed:", e)

    return ev


@router.post("/events/{event_id}/confirm", response_model=EventOut, dependencies=[Depends(require_admin_api_key)])
def confirm_event(
    event_id: int = Path(...),
    db: Session = Depends(get_db)
):
    ev = db.query(Event).filter(Event.event_id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    ev.confirmed = True
    db.add(ev)
    db.commit()
    return ev