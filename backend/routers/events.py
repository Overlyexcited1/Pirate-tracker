# backend/routers/events.py
from fastapi import APIRouter, Depends, HTTPException, Path, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from models import Event
from schemas import EventCreate, EventOut
from deps import require_client_api_key, require_admin_api_key
import crud

# import the org enrichment background task
from tasks import enrich_attacker_org

router = APIRouter(tags=["events"])

@router.post("/events", response_model=EventOut, dependencies=[Depends(require_client_api_key)])
def post_event(payload: EventCreate, bg: BackgroundTasks, db: Session = Depends(get_db)):
    # upsert attacker & victim players
    attacker = crud.get_or_create_player(db, payload.attacker_id, payload.attacker_name, org=payload.attacker_org)
    victim   = crud.get_or_create_player(db, payload.victim_id, payload.victim_name)

    # create event (your existing CRUD packs coordinates/damage_type/etc.)
    ev = crud.create_event(db, payload)
    ev.attacker = attacker
    ev.victim   = victim
    db.commit()

    # update stats
    crud.update_player_stats(db, attacker, victim, ev)
    db.commit()

    # kick off org enrichment if attacker_org is missing/empty
    if not payload.attacker_org:
        bg.add_task(enrich_attacker_org, payload.attacker_name, getattr(attacker, "player_id", None))

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