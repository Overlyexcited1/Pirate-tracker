from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Player(Base):
    __tablename__ = "players"
    player_id = Column(Integer, primary_key=True, index=True, nullable=True)
    name = Column(String, unique=False, index=True)
    org = Column(String, nullable=True, index=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_attacks = Column(Integer, default=0)
    total_kills = Column(Integer, default=0)
    value_destroyed = Column(Float, default=0.0)
    score = Column(Float, default=0.0)
    events_as_attacker = relationship("Event", back_populates="attacker", foreign_keys="Event.attacker_id")
    events_as_victim = relationship("Event", back_populates="victim", foreign_keys="Event.victim_id")

class Event(Base):
    __tablename__ = "events"
    event_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(String, index=True)
    attacker_id = Column(Integer, ForeignKey("players.player_id"), nullable=True)
    attacker_name = Column(String, index=True)
    attacker_org = Column(String, index=True, nullable=True)
    victim_id = Column(Integer, ForeignKey("players.player_id"), nullable=True)
    victim_name = Column(String, index=True)
    zone = Column(String)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    z = Column(Float, nullable=True)
    weapon = Column(String, nullable=True)
    damage_type = Column(String)
    ship_value_estimate = Column(Float, default=0.0)
    raw_line = Column(Text)
    confirmed = Column(Boolean, default=True)
    attacker = relationship("Player", foreign_keys=[attacker_id], back_populates="events_as_attacker")
    victim = relationship("Player", foreign_keys=[victim_id], back_populates="events_as_victim")
