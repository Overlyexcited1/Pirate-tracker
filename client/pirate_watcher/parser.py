\
import re
from typing import Optional, Dict

LINE_RE = re.compile(
    r"<(?P<ts>[^>]+)>\s*\[Notice\]\s*<Actor Death>\s*CActor::Kill:\s*'(?P<victim>[^']+)'\s*\[(?P<victim_id>\d+)\]\s*in zone\s*'(?P<zone>[^']+)'\s*killed by\s*(?P<attacker_part>[^\[]+?)\s*\[(?P<attacker_id>\d+)\].*?damage type\s*'(?P<damage>[^']+)'.*?x:\s*(?P<x>-?\d+(?:\.\d+)?),\s*y:\s*(?P<y>-?\d+(?:\.\d+)?),\s*z:\s*(?P<z>-?\d+(?:\.\d+)?)",
    re.IGNORECASE
)

def _split_attacker(part: str):
    part = part.strip()
    if '(' in part and ')' in part:
        try:
            name, rest = part.split('(',1)
            org = rest.split(')',1)[0].strip()
            return name.strip(), org or None
        except Exception:
            return part, None
    return part, None

def parse_line(line: str) -> Optional[Dict]:
    m = LINE_RE.search(line)
    if not m:
        return None
    gd = m.groupdict()
    attacker_name_raw = gd.get('attacker_part','').strip()
    attacker_name, attacker_org = _split_attacker(attacker_name_raw)
    return {
        "timestamp": gd["ts"],
        "victim_name": gd["victim"],
        "victim_id": int(gd["victim_id"]),
        "attacker_name": attacker_name,
        "attacker_id": int(gd["attacker_id"]),
        "attacker_org": attacker_org,
        "zone": gd["zone"],
        "weapon": None,
        "damage_type": gd["damage"],
        "coords": {"x": float(gd["x"]), "y": float(gd["y"]), "z": float(gd["z"])},
        "source_line": line.strip(),
    }
