from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Player
import os
from dotenv import load_dotenv
load_dotenv()
router = APIRouter(tags=['roster'])

@router.get('/roster')
def get_roster(db: Session = Depends(get_db)):
    ORG_NAME = os.getenv('ORG_NAME','').strip()
    if ORG_NAME:
        players = db.query(Player).filter(Player.org == ORG_NAME).all()
        if players:
            return {'roster':[p.name for p in players]}
    roster_env = os.getenv('ROSTER_MEMBERS','')
    if roster_env:
        roster = [s.strip() for s in roster_env.split(',') if s.strip()]
        return {'roster': roster}
    return {'roster': []}
