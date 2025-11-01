# backend/crud.py
from sqlalchemy.orm import Session
from backend.models import Player, Event

def get_player_by_name(db: Session, name: str) -> Player | None:
    return db.query(Player).filter(Player.name == name).first()

def get_or_create_player_by_name(db: Session, name: str) -> Player:
    p = get_player_by_name(db, name)
    if p:
        return p
    p = Player(name=name)
    db.add(p)
    db.flush()
    return p

def create_event(db: Session, payload) -> Event:
    ev = Event(
        timestamp=payload.timestamp,
        # denormalized names + org right on the Event row:
        attacker_name=payload.attacker_name,
        attacker_org=payload.attacker_org,
        victim_name=payload.victim_name,

        zone=payload.zone,
        x=payload.coords.x,
        y=payload.coords.y,
        z=payload.coords.z,
        weapon=payload.weapon,
        damage_type=payload.damage_type,
        ship_value_estimate=payload.ship_value_estimate,
        raw_line=payload.source_line,  # <— map source_line -> raw_line
        # confirmed defaults True in your model; no need to pass it unless you want to override
    )
    db.add(ev)
    db.flush()  # allocates event_id
    return ev

def update_player_stats(db: Session, attacker: Player, victim: Player, ev: Event) -> None:
    attacker.total_kills = (attacker.total_kills or 0) + 1
    attacker.total_attacks = (attacker.total_attacks or 0) + 1
    attacker.value_destroyed = (attacker.value_destroyed or 0) + (ev.ship_value_estimate or 0.0)
    victim.total_attacks = (victim.total_attacks or 0) + 1
    db.add(attacker)
    db.add(victim)