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

@router.post(
    "/events",
    response_model=EventOut,
    dependencies=[Depends(require_client_api_key)],
)
def post_event(
    payload: EventCreate,
    background_tasks: BackgroundTasks,          # non-default first
    db: Session = Depends(get_db),              # default (Depends) after
):
    attacker = crud.get_or_create_player_by_name(db, payload.attacker_name)
    victim   = crud.get_or_create_player_by_name(db, payload.victim_name)

    ev = Event(
        timestamp=payload.timestamp,
        attacker_id=attacker.player_id if attacker else None,
        victim_id=victim.player_id if victim else None,
        attacker_name=payload.attacker_name,
        attacker_org=payload.attacker_org,
        victim_name=payload.victim_name,
        zone=payload.zone,
        x=(payload.coords.x if payload.coords else None),
        y=(payload.coords.y if payload.coords else None),
        z=(payload.coords.z if payload.coords else None),
        weapon=payload.weapon,
        damage_type=payload.damage_type,
        ship_value_estimate=payload.ship_value_estimate or 0.0,
        raw_line=payload.source_line,
        confirmed=True,
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    try:
        crud.update_player_stats(db, attacker, victim, ev)
        db.commit()
    except Exception:
        db.rollback()

    if not payload.attacker_org and payload.attacker_name:
        background_tasks.add_task(enrich_attacker_org, payload.attacker_name, None)

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