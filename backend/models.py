# models.py
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, func, UniqueConstraint
)
from sqlalchemy.orm import relationship, backref
from datetime import datetime
from backend.database import Base

# ---------------------------------------------------------------------
# ORGANIZATION (metadata for each org, keyed by SID)
# ---------------------------------------------------------------------
class Organization(Base):
    __tablename__ = "organizations"

    # CIG org SID, e.g., "03B" (primary key)
    sid = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True, index=True)
    logo = Column(String, nullable=True)
    url = Column(String, nullable=True)
    member_count = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # reverse: members in this org (via link table)
    players = relationship(
        "Player",
        secondary="player_organizations",
        back_populates="organizations",
        lazy="selectin",
    )

# ---------------------------------------------------------------------
# PLAYER (your original schema — preserved)
# ---------------------------------------------------------------------
class Player(Base):
    __tablename__ = "players"

    # your original PK name
    player_id = Column(Integer, primary_key=True, index=True, nullable=True)

    # original columns kept intact
    name = Column(String, unique=False, index=True)
    org = Column(String, nullable=True, index=True)  # legacy single-org string (kept for compatibility)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    total_attacks = Column(Integer, default=0)
    total_kills = Column(Integer, default=0)
    value_destroyed = Column(Float, default=0.0)
    score = Column(Float, default=0.0)

    # events (your original relationships)
    events_as_attacker = relationship(
        "Event",
        back_populates="attacker",
        foreign_keys="Event.attacker_id",
        lazy="selectin",
    )
    events_as_victim = relationship(
        "Event",
        back_populates="victim",
        foreign_keys="Event.victim_id",
        lazy="selectin",
    )

    # NEW: many-to-many to organizations via link table
    org_links = relationship(
        "PlayerOrganization",
        back_populates="player",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    organizations = relationship(
        "Organization",
        secondary="player_organizations",
        back_populates="players",
        lazy="selectin",
    )

# ---------------------------------------------------------------------
# LINK TABLE: PLAYER <-> ORGANIZATION (many-to-many, up to 6 orgs)
# ---------------------------------------------------------------------
class PlayerOrganization(Base):
    __tablename__ = "player_organizations"

    id = Column(Integer, primary_key=True, index=True)

    # FKs
    player_id = Column(Integer, ForeignKey("players.player_id", ondelete="CASCADE"), nullable=False, index=True)
    org_sid   = Column(String,  ForeignKey("organizations.sid", ondelete="CASCADE"), nullable=False, index=True)

    # org-specific metadata for this player
    is_primary = Column(Boolean, default=False, index=True)  # main org flag
    rank       = Column(String, nullable=True)               # e.g., rank name
    role       = Column(String, nullable=True)               # e.g., "Scout", "Officer"
    source     = Column(String, nullable=True)               # e.g., "starapi", "manual", "discord"
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    player = relationship("Player", back_populates="org_links", lazy="joined")
    organization = relationship("Organization", lazy="joined")

    __table_args__ = (
        UniqueConstraint("player_id", "org_sid", name="uq_player_org_unique"),
    )

# ---------------------------------------------------------------------
# EVENT (your original schema — preserved)
# ---------------------------------------------------------------------
class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # you originally stored ISO strings; keep that for compatibility
    timestamp = Column(String, index=True)

    # attacker/victim FKs to players
    attacker_id = Column(Integer, ForeignKey("players.player_id"), nullable=True)
    victim_id   = Column(Integer, ForeignKey("players.player_id"), nullable=True)

    # denormalized names/orgs (keep — useful for quick queries & historical snapshots)
    attacker_name = Column(String, index=True)
    attacker_org  = Column(String, index=True, nullable=True)
    victim_name   = Column(String, index=True)

    # location & context
    zone = Column(String)
    x = Column(Float, nullable=True)
    y = Column(Float, nullable=True)
    z = Column(Float, nullable=True)
    weapon = Column(String, nullable=True)
    damage_type = Column(String)
    ship_value_estimate = Column(Float, default=0.0)

    # raw line + confirmation
    raw_line = Column(Text)
    confirmed = Column(Boolean, default=True)

    # relationships back to Player
    attacker = relationship("Player", foreign_keys=[attacker_id], back_populates="events_as_attacker", lazy="joined")
    victim   = relationship("Player", foreign_keys=[victim_id],   back_populates="events_as_victim",   lazy="joined")
