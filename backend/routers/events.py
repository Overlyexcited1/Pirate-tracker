# backend/routers/events.py
from fastapi import APIRouter, Depends, HTTPException, Path, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Event
from backend.schemas import EventCreate, EventOut
from backend.deps import require_client_api_key, require_admin_api_key
import backend.crud as crud

try:
    from backend.tasks import enrich_attacker_org
except Exception:
    def enrich_attacker_org(*args, **kwargs): return None

router = APIRouter(tags=["events"])

@router.post("/events", response_model=EventOut, dependencies=[Depends(require_client_api_key)])
def post_event(payload: EventCreate, db: Session = Depends(get_db), bg: BackgroundTasks | None = None):
    # ensure Players exist (by name) and wire FKs
    attacker = crud.get_or_create_player_by_name(db, payload.attacker_name)
    victim   = crud.get_or_create_player_by_name(db, payload.victim_name)

    ev = crud.create_event(db, payload)
    ev.attacker_id = attacker.player_id
    ev.victim_id   = victim.player_id
    db.add(ev)
    db.commit()

    crud.update_player_stats(db, attacker, victim, ev)
    db.commit()

    # optional enrichment if org missing
    if bg and not payload.attacker_org:
        bg.add_task(enrich_attacker_org, payload.attacker_name, None)

    return ev

@router.post("/events/{event_id}/confirm", response_model=EventOut, dependencies=[Depends(require_admin_api_key)])
def confirm_event(event_id: int = Path(...), db: Session = Depends(get_db)):
    ev = db.query(Event).filter(Event.event_id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    ev.confirmed = True
    db.add(ev)
    db.commit()
    return ev