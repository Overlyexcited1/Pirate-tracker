from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Event
from math import sqrt
from collections import Counter
router = APIRouter(tags=['heatmap'])

# Replace these with real coordinates for accuracy
BODIES = {
    'Crusader': (0.0, 0.0, 0.0),
    'Daymar': (10000.0, 5000.0, 0.0),
    'Yela': (-8000.0, -3000.0, 2000.0),
    'Cellin': (4000.0, -7000.0, -1000.0),
    'MicroTech': (20000.0, 10000.0, 0.0),
    'Bennu': (-15000.0, 12000.0, 3000.0),
}

def _nearest_body(x: float, y: float, z: float):
    best = None
    best_dist = None
    for name, (bx, by, bz) in BODIES.items():
        d = ((x-bx)**2 + (y-by)**2 + (z-bz)**2) ** 0.5
        if best_dist is None or d < best_dist:
            best = name
            best_dist = d
    return best, best_dist

@router.get('/heatmap')
def heatmap(db: Session = Depends(get_db)):
    events = db.query(Event).filter(Event.confirmed == True).all()
    counts = Counter()
    nearest_samples = {}
    for e in events:
        if e.x is None or e.y is None or e.z is None:
            continue
        body, dist = _nearest_body(e.x, e.y, e.z)
        counts[body] += 1
        if body not in nearest_samples or dist < nearest_samples[body][1]:
            nearest_samples[body] = ((e.x, e.y, e.z), dist)
    summary = [{'body': b, 'count': counts[b], 'sample_coord': nearest_samples.get(b, (None, None))[0]} for b in counts]
    summary = sorted(summary, key=lambda x: x['count'], reverse=True)
    return {'hotspots': summary}
