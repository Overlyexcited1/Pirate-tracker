# backend/crud.py
from sqlalchemy.orm import Session
from backend.models import Player, Event
from backend.schemas import EventCreate

# --- Players ---

def get_player_by_name(db: Session, name: str) -> Player | None:
    return db.query(Player).filter(Player.name == name).first()

def create_player(db: Session, name: str) -> Player:
    p = Player(name=name)
    db.add(p)
    db.flush()          # populate p.player_id without full commit
    return p

def get_or_create_player(db: Session, name: str) -> Player:
    p = get_player_by_name(db, name)
    if p:
        return p
    return create_player(db, name)

# --- Events ---

# --- Events ---

def create_event(db: Session, payload: EventCreate) -> Event:
    ev = Event(
        timestamp=payload.timestamp,
        zone=payload.zone,
        x=payload.coords.x,
        y=payload.coords.y,
        z=payload.coords.z,
        weapon=payload.weapon,
        damage_type=payload.damage_type,
        # CHANGE: use the actual column name on Event
        ship_value_estimate=payload.ship_value_estimate,
        source_line=payload.source_line,
        confirmed=False,
    )
    db.add(ev)
    db.flush()
    return ev

def update_player_stats(db: Session, attacker: Player, victim: Player, ev: Event) -> None:
    attacker.total_kills = (attacker.total_kills or 0) + 1
    attacker.total_attacks = (attacker.total_attacks or 0) + 1
    # CHANGE: pull from the event's real field name
    attacker.value_destroyed = (attacker.value_destroyed or 0) + (getattr(ev, "ship_value_estimate", 0) or 0)

    victim.total_attacks = (victim.total_attacks or 0) + 1

    db.add(attacker)
    db.add(victim)