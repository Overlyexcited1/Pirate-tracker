from sqlalchemy.orm import Session
from backend.models import Player
from datetime import datetime
def decay_factor(days_since_last: float) -> float:
    return 0.05 * days_since_last
def recompute_scores(db: Session):
    now = datetime.utcnow()
    players = db.query(Player).all()
    for p in players:
        days = max(0.0, (now - p.last_seen).total_seconds() / 86400.0)
        p.score = 2 * p.total_kills + 1 * p.total_attacks + (p.value_destroyed / 100000.0) - decay_factor(days)
        db.add(p)
    db.flush()
    db.commit()
