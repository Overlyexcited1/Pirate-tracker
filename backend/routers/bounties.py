from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Player
from backend.schemas import PirateProfile
from services_ranking import recompute_scores

router = APIRouter(tags=["bounties"])

@router.get("/bounties", response_model=list[PirateProfile])
def get_bounties(db: Session = Depends(get_db), limit: int = 25):
    recompute_scores(db)
    q = db.query(Player).order_by(Player.score.desc()).limit(limit).all()
    return [PirateProfile(player_id=p.player_id or 0, name=p.name, org=p.org, total_attacks=p.total_attacks, total_kills=p.total_kills, value_destroyed=p.value_destroyed, score=p.score) for p in q]
