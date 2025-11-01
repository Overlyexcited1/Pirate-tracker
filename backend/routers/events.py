from fastapi import APIRouter, Depends, HTTPException, Path, BackgroundTasks
from sqlalchemy.orm import Session

from backend.database import get_db  # do NOT import Base/engine here
from backend.models import Event
from backend.schemas import EventCreate, EventOut
from backend.deps import require_client_api_key, require_admin_api_key
import backend.crud as crud

# tasks is optional; if it's missing or services aren't wired, make it a no-op
try:
    from backend.tasks import enrich_attacker_org
except Exception:
    def enrich_attacker_org(*args, **kwargs):
        return None

router = APIRouter(tags=["events"])

@router.post("/events", response_model=EventOut, dependencies=[Depends(require_client_api_key)])
def post_event(payload: EventCreate, db: Session = Depends(get_db), bg: BackgroundTasks = None):
    try:
        # 1) Upsert players (DO NOT pass org kwarg)
        attacker = crud.get_or_create_player(db, payload.attacker_id, payload.attacker_name)
        victim   = crud.get_or_create_player(db, payload.victim_id,   payload.victim_name)

        # If your Player model has an 'org' column and you want to save it:
        if getattr(attacker, "org", None) is not None and payload.attacker_org:
            attacker.org = payload.attacker_org  # simple assign on model
            db.add(attacker)

        db.flush()  # ensure IDs exist

        # 2) Build Event with FK IDs set up-front
        ev = Event(
            timestamp=payload.timestamp,
            zone=payload.zone,
            x=payload.coords.x,
            y=payload.coords.y,
            z=payload.coords.z,
            weapon=payload.weapon,
            damage_type=payload.damage_type,           # must match your Enum
            ship_value_estimate=payload.ship_value_estimate,
            source_line=payload.source_line,
            attacker_id=attacker.player_id,
            victim_id=victim.player_id,
            attacker_org=payload.attacker_org or None  # nullable is fine
        )
        db.add(ev)
        db.flush()

        # 3) Update stats
        crud.update_player_stats(db, attacker, victim, ev)

        db.commit()
        db.refresh(ev)

        # 4) Optional enrichment if org not provided
        if bg and not payload.attacker_org:
            bg.add_task(enrich_attacker_org, payload.attacker_name, None)

        return ev

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/events/{event_id}/confirm", response_model=EventOut, dependencies=[Depends(require_admin_api_key)])
def confirm_event(event_id: int = Path(...), db: Session = Depends(get_db)):
    ev = db.query(Event).filter(Event.event_id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    ev.confirmed = True
    db.add(ev)
    db.commit()
    return ev