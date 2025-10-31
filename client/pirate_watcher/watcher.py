import time, os
from pathlib import Path
from collections import deque
from .parser import parse_line
from .api import post_event, get_roster
from dotenv import load_dotenv
load_dotenv()

ORG_ROSTER = set([s.strip() for s in os.getenv('ORG_ROSTER','').split(',') if s.strip()])

def run_watcher(log_path: str = None):
    path = Path(log_path or os.getenv('LOG_PATH', ''))
    if not path.exists():
        print('Log path not found:', path)
        return
    print('Watching:', path)

    if os.getenv('FETCH_ROSTER','1') == '1':
        try:
            roster = get_roster()
            if roster:
                print('Fetched roster:', roster)
                ORG_ROSTER.clear()
                ORG_ROSTER.update(roster)
        except Exception as e:
            print('Roster fetch failed:', e)

    seen = deque(maxlen=200)
    with path.open('r', encoding='utf-8', errors='ignore') as f:
        f.seek(0,2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2); continue
            data = parse_line(line)
            if not data: continue
            victim = data['victim_name']; attacker = data['attacker_name']
            if ORG_ROSTER and (victim in ORG_ROSTER) and (attacker not in ORG_ROSTER):
                key = (data['timestamp'], attacker, victim)
                if key in seen: continue
                seen.append(key)
                payload = {
                    'timestamp': data['timestamp'],
                    'attacker_name': data['attacker_name'],
                    'attacker_id': data.get('attacker_id'),
                    'attacker_org': data.get('attacker_org'),
                    'victim_name': data['victim_name'],
                    'victim_id': data.get('victim_id'),
                    'zone': data['zone'],
                    'coords': data['coords'],
                    'weapon': data.get('weapon'),
                    'damage_type': data['damage_type'],
                    'ship_value_estimate': 0.0,
                    'source_line': data['source_line'],
                }
                try:
                    resp = post_event(payload)
                    print('Submitted event', resp.get('event_id'), '->', attacker, 'near', data['coords'])
                except Exception as e:
                    print('Submit failed:', e)
