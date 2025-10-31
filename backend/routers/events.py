from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from models import Event
from schemas import EventCreate, EventOut
from deps import require_client_api_key, require_admin_api_key
import crud

Base.metadata.create_all(bind=engine)
router = APIRouter(tags=["events"])

@router.post("/events", response_model=EventOut, dependencies=[Depends(require_client_api_key)])
def post_event(payload: EventCreate, db: Session = Depends(get_db)):
    attacker = crud.get_or_create_player(db, payload.attacker_id, payload.attacker_name, org=payload.attacker_org)
    victim = crud.get_or_create_player(db, payload.victim_id, payload.victim_name)
    ev = crud.create_event(db, payload)
    ev.attacker = attacker
    ev.victim = victim
    db.commit()
    crud.update_player_stats(db, attacker, victim, ev)
    db.commit()
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
