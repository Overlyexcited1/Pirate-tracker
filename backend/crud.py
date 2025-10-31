from sqlalchemy.orm import Session
from models import Player, Event
from typing import Optional
from datetime import datetime

def get_or_create_player(db: Session, player_id: Optional[int], name: str, org: Optional[str]=None) -> Player:
    obj = None
    if player_id is not None:
        obj = db.query(Player).filter(Player.player_id == player_id).first()
    if obj is None:
        obj = db.query(Player).filter(Player.name == name).first()
    if obj is None:
        obj = Player(player_id=player_id if player_id is not None else None, name=name, org=org)
        db.add(obj)
        db.flush()
    if org:
        obj.org = org
    obj.last_seen = datetime.utcnow()
    return obj

def create_event(db: Session, data) -> Event:
    ev = Event(
        timestamp=data.timestamp,
        attacker_id=data.attacker_id,
        attacker_name=data.attacker_name,
        attacker_org=data.attacker_org,
        victim_id=data.victim_id,
        victim_name=data.victim_name,
        zone=data.zone,
        x=data.coords.x,
        y=data.coords.y,
        z=data.coords.z,
        weapon=data.weapon,
        damage_type=data.damage_type,
        ship_value_estimate=data.ship_value_estimate or 0.0,
        raw_line=data.source_line,
        confirmed=True,
    )
    db.add(ev)
    db.flush()
    return ev

def update_player_stats(db: Session, attacker: Player, victim: Player, ev: Event):
    is_kill = ("death" in (ev.damage_type or "").lower()) or ("destruction" in (ev.damage_type or "").lower())
    attacker.total_attacks += 1
    if is_kill:
        attacker.total_kills += 1
    attacker.value_destroyed += ev.ship_value_estimate or 0.0
    db.add(attacker)
    if victim:
        db.add(victim)

def confirm_event(db: Session, ev: Event, confirmed: bool):
    ev.confirmed = confirmed
    db.add(ev)
    return ev
