from pydantic import BaseModel
from typing import Optional

class Coords(BaseModel):
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
    coords: Coords
    weapon: Optional[str] = None
    damage_type: str
    ship_value_estimate: Optional[float] = 0.0
    source_line: str

class EventOut(BaseModel):
    event_id: int
    timestamp: str
    attacker_name: str
    attacker_id: Optional[int]
    attacker_org: Optional[str]
    victim_name: str
    victim_id: Optional[int]
    zone: str
    x: Optional[float]
    y: Optional[float]
    z: Optional[float]
    weapon: Optional[str]
    damage_type: str
    ship_value_estimate: float
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
