# backend/tasks.py
from contextlib import contextmanager
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Organization
# OLD: from services.starapi import fetch_user_org, fetch_org_info
from .services.starapi import fetch_user_org, fetch_org_info

@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

def upsert_org(db: Session, org_meta: dict):
    if not org_meta or not org_meta.get("sid"):
        return
    sid = org_meta["sid"]
    org = db.get(Organization, sid)  # SQLAlchemy 2.x style; use query().get() if on 1.4
    if org is None:
        org = Organization(sid=sid)
        db.add(org)
    for k in ("name", "logo", "url", "member_count"):
        v = org_meta.get(k)
        if v is not None:
            setattr(org, k, v)

def enrich_attacker_org(attacker_handle: str, attacker_player_id: int | None = None):
    """Look up attacker's org via starcitizen-api and persist Organization (and optionally link Player)."""
    try:
        u = fetch_user_org(attacker_handle)
        if not u or not u.get("sid"):
            return
        meta = fetch_org_info(u["sid"]) or {"sid": u["sid"], "name": u.get("name")}
        with session_scope() as db:
            upsert_org(db, meta)
            # OPTIONAL (for later many-to-many linkage):
            # if attacker_player_id:
            #     from models import Player, PlayerOrganization
            #     p = db.get(Player, attacker_player_id)
            #     if p:
            #         # create PlayerOrganization link here...
            #         pass
    except Exception as e:
        print("enrich_attacker_org failed:", e)
