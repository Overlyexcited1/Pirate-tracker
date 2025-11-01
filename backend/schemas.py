# backend/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class Coord3D(BaseModel):
    x: float
    y: float
    z: float

class EventCreate(BaseModel):
    timestamp: str
    attacker_name: str
    attacker_id: Optional[int] = None
    attacker_org: Optional[str] = None
    victim_name: str
    victim_id: Optional[int] = None
    zone: str
    coords: Coord3D
    weapon: Optional[str] = None
    damage_type: str
    ship_value_estimate: float = 0.0
    source_line: Optional[str] = Field(default=None)   # maps to Event.raw_line

class EventOut(BaseModel):
    event_id: int
    timestamp: str
    attacker_id: Optional[int]
    victim_id: Optional[int]
    attacker_name: str
    attacker_org: Optional[str]
    victim_name: str
    zone: str
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    weapon: Optional[str]
    damage_type: str
    ship_value_estimate: float
    raw_line: Optional[str]
    confirmed: bool

    class Config:
        from_attributes = True


class PirateProfile(BaseModel):
    player_id: int
    name: str
    org: Optional[str] = None
    total_attacks: int
    total_kills: int
    value_destroyed: float
    score: float
