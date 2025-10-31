from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Player
from schemas import PirateProfile
router = APIRouter(tags=['players'])

@router.get('/pirates/by-name', response_model=PirateProfile)
def get_pirate_by_name(name: str = Query(...), db: Session = Depends(get_db)):
    p = db.query(Player).filter(Player.name == name).first()
    if not p:
        raise HTTPException(status_code=404, detail='Not found')
    return PirateProfile(player_id=p.player_id or 0, name=p.name, org=p.org, total_attacks=p.total_attacks, total_kills=p.total_kills, value_destroyed=p.value_destroyed, score=p.score)
    
@router.get('/pirates/{player_id}', response_model=PirateProfile)
def get_pirate(player_id: int, db: Session = Depends(get_db)):
    p = db.query(Player).filter(Player.player_id == player_id).first()
    if not p:
        raise HTTPException(status_code=404, detail='Not found')
    return PirateProfile(player_id=p.player_id or 0, name=p.name, org=p.org, total_attacks=p.total_attacks, total_kills=p.total_kills, value_destroyed=p.value_destroyed, score=p.score)
