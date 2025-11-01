# bot.py — Bulwark Pirate Tracker (async HTTP, full command set incl. /postevent)

import os
import time
import json
import asyncio
import datetime as dt
from urllib.parse import quote_plus

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# ---------- load env ----------
load_dotenv()
DISCORD_TOKEN  = os.getenv("DISCORD_TOKEN", "")
BACKEND_URL    = os.getenv("BACKEND_URL", "").rstrip("/")
API_PREFIX     = os.getenv("API_PREFIX", "/api/v1").strip()
GUILD_ID       = os.getenv("GUILD_ID")     # string ok
OWNER_ID       = os.getenv("OWNER_ID")     # optional
CLIENT_API_KEY = os.getenv("CLIENT_API_KEY", "").strip()

# auto-correct common typo
if API_PREFIX.lower().rstrip("/") == "/api/vi":
    print("NOTE: corrected '/api/vi' to '/api/v1'")
    API_PREFIX = "/api/v1"

if not API_PREFIX.startswith("/"):
    API_PREFIX = "/" + API_PREFIX
API_PREFIX = API_PREFIX.rstrip("/")

# ---------- discord setup ----------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

session: aiohttp.ClientSession | None = None
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=20)

# ---------- http helpers ----------
def _full_url(path: str) -> str:
    # path should be like "/events" or "events"
    return f"{BACKEND_URL}{API_PREFIX}{path if path.startswith('/') else '/' + path}"

async def http_get_json(path: str, timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT):
    """GET -> (json_or_text, err)"""
    global session
    if not BACKEND_URL:
        return None, "Backend URL missing."
    if session is None or session.closed:
        session = aiohttp.ClientSession(timeout=timeout)

    url = _full_url(path)
    try:
        async with session.get(url) as resp:
            if resp.status >= 400:
                return None, f"{resp.status}: {(await resp.text())[:300]}"
            try:
                return await resp.json(), None
            except aiohttp.ContentTypeError:
                return await resp.text(), None
    except asyncio.TimeoutError:
        return None, "Backend timed out."
    except aiohttp.ClientConnectionError:
        return None, "Cannot reach backend."
    except Exception as e:
        return None, f"HTTP error: {e}"

async def http_post_json(path: str, payload: dict, use_client_key: bool = True,
                         timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT):
    """POST JSON -> (json_or_text, err)"""
    global session
    if not BACKEND_URL:
        return None, "Backend URL missing."
    if session is None or session.closed:
        session = aiohttp.ClientSession(timeout=timeout)

    headers = {"Content-Type": "application/json"}
    if use_client_key and CLIENT_API_KEY:
        headers["x-client-api-key"] = CLIENT_API_KEY

    url = _full_url(path)
    try:
        async with session.post(url, json=payload, headers=headers) as resp:
            txt = await resp.text()
            if resp.status >= 400:
                return None, f"{resp.status}: {txt[:300]}"
            try:
                return await resp.json(), None
            except aiohttp.ContentTypeError:
                return txt, None
    except asyncio.TimeoutError:
        return None, "Backend timed out."
    except aiohttp.ClientConnectionError:
        return None, "Cannot reach backend."
    except Exception as e:
        return None, f"HTTP error: {e}"

# ---------- formatting helpers ----------
def _extract_rows(payload, key_candidates=("hotspots","bounties","roster","data","items")):
    if payload is None:
        return []
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            return [{"body": payload}]
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for k in key_candidates:
            v = payload.get(k)
            if isinstance(v, list):
                return v
        return payload.get("rows") or payload.get("result") or []
    return []

def fmt_hotspots(payload):
    rows = _extract_rows(payload, ("hotspots","data","items"))
    if not rows:
        return payload if isinstance(payload, str) else "No incidents yet. 💤"
    lines = ["**Hotspots (last 7 days):**"]
    for r in rows:
        if isinstance(r, str):
            lines.append(f"• {r}")
            continue
        body = r.get("body") or r.get("name") or "Unknown"
        count = r.get("count") or r.get("events")
        lines.append(f"• **{body}**" + (f" — {count} attacks" if count else ""))
    return "\n".join(lines)

def fmt_bounties(payload):
    rows = _extract_rows(payload, ("bounties","data","items"))
    if not rows:
        return payload if isinstance(payload, str) else "No bounties yet."
    lines = ["**Top Bounties:**"]
    for i, r in enumerate(rows, 1):
        if isinstance(r, str):
            lines.append(f"{i}. {r}")
            continue
        name  = r.get("name") or r.get("player") or "Unknown"
        org   = r.get("org") or r.get("organization") or "—"
        score = r.get("score") or r.get("count") or 0
        lines.append(f"{i}. **{name}** ({org}) — {score} pts")
    return "\n".join(lines)

def fmt_pirate(payload, query):
    if isinstance(payload, str):
        return payload
    d = payload.get("pirate", payload) if payload else None
    if not d:
        return f"No record found for **{query}**."
    name   = d.get("name") or query
    org    = d.get("org") or d.get("organization") or "—"
    total  = d.get("incidents") or d.get("count") or 0
    last   = d.get("last_seen") or "unknown"
    bodies = d.get("hotspots") or []
    where  = ", ".join(f"{b.get('body','?')}({b.get('count',0)})" for b in bodies) if bodies else "—"
    return f"**{name}** ({org})\nIncidents: **{total}**\nLast seen: {last}\nHotspots: {where}"

def fmt_roster(payload):
    rows = _extract_rows(payload, ("roster","data","items"))
    if not rows:
        return payload if isinstance(payload, str) else "No roster data."
    lines = ["**Org Roster (summary):**"]
    for r in rows[:20]:
        if isinstance(r, str):
            lines.append(f"• {r}")
            continue
        name = r.get("name") or r.get("handle") or "Unknown"
        role = r.get("role") or r.get("rank") or "—"
        lines.append(f"• **{name}** — {role}")
    if len(rows) > 20:
        lines.append(f"...and {len(rows)-20} more.")
    return "\n".join(lines)

# ---------- lifecycle ----------
@bot.event
async def on_ready():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT)
    print(f"✅ Bot ready as {bot.user}")
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"Guild sync: {len(synced)} commands -> {[c.name for c in synced]}")
        else:
            synced = await bot.tree.sync()
            print(f"Global sync: {len(synced)} commands")
    except Exception as e:
        print(f"⚠️ Sync failed: {e}")

@bot.event
async def on_close():
    if session and not session.closed:
        await session.close()

# ---------- global slash error hook ----------
@bot.tree.error
async def on_app_command_error(inter: discord.Interaction, error: Exception):
    msg = f"⚠️ Error: {error}"
    try:
        if inter.response.is_done():
            await inter.followup.send(msg, ephemeral=True)
        else:
            await inter.response.send_message(msg, ephemeral=True)
    finally:
        print("Slash command error:", repr(error))

# ---------- admin tools ----------
def is_admin(inter: discord.Interaction) -> bool:
    perms = getattr(inter.user, "guild_permissions", None)
    return bool(perms and perms.administrator)

@bot.tree.command(name="resync", description="Force-refresh slash commands in this server (admin only)")
async def resync_cmd(inter: discord.Interaction):
    if not is_admin(inter):
        await inter.response.send_message("Admins only.", ephemeral=True)
        return
    await inter.response.defer(ephemeral=True)
    try:
        if not GUILD_ID or int(GUILD_ID) != inter.guild_id:
            await inter.followup.send("Set GUILD_ID in .env to THIS server id, then restart the bot.")
            return
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.clear_commands(guild=guild)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        await inter.followup.send(f"Resynced **{len(synced)}** cmds: {', '.join(c.name for c in synced)}")
    except Exception as e:
        await inter.followup.send(f"Resync failed: {e}")

@bot.tree.command(name="debug", description="Show bot config & loaded commands (ephemeral)")
async def debug_cmd(inter: discord.Interaction):
    await inter.response.defer(ephemeral=True)
    cmds = [c.name for c in bot.tree.get_commands()]
    msg = (
        f"BACKEND_URL: {BACKEND_URL}\n"
        f"API_PREFIX:  {API_PREFIX}\n"
        f"GUILD_ID:    {GUILD_ID}\n"
        f"Loaded cmds: {len(cmds)} -> {', '.join(cmds)}"
    )
    await inter.followup.send(msg)

# ---------- small utilities ----------
@bot.tree.command(name="ping", description="Quick bot health check")
async def ping_cmd(inter: discord.Interaction):
    await inter.response.send_message("pong ✅", ephemeral=True)

@bot.tree.command(name="health", description="Backend health check")
async def health_cmd(inter: discord.Interaction):
    await inter.response.defer(ephemeral=True)
    try:
        global session
        if session is None or session.closed:
            session = aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT)
        # Hit versioned health if your backend exposes it there; otherwise change to "/health"
        async with session.get(_full_url("/health")) as resp:
            txt = await resp.text()
            await inter.followup.send(f"{resp.status}: {txt[:200]}")
    except Exception as e:
        await inter.followup.send(f"Health failed: {e}")

# ---------- generic GET helper ----------
async def _send(inter: discord.Interaction, path: str, fmt_fn):
    await inter.response.defer(ephemeral=True)
    t0 = time.time()
    data, err = await http_get_json(path)
    if err:
        await inter.followup.send(f"⚠️ {err}")
        return
    try:
        msg = fmt_fn(data)
    except Exception as e:
        msg = f"⚠️ Format error: {e}"
    await inter.followup.send(f"{msg}\n_(query {time.time()-t0:.1f}s)_")

# ---------- commands ----------
@bot.tree.command(name="heatmap", description="Show piracy hotspots")
async def heatmap_cmd(inter: discord.Interaction):
    await _send(inter, "/heatmap", fmt_hotspots)

@bot.tree.command(name="hotspots", description="Alias for /heatmap")
async def hotspots_cmd(inter: discord.Interaction):
    await _send(inter, "/heatmap", fmt_hotspots)

@bot.tree.command(name="bounties", description="Show top pirates")
async def bounties_cmd(inter: discord.Interaction):
    await _send(inter, "/bounties", fmt_bounties)

@bot.tree.command(name="board", description="Alias for /bounties")
async def board_cmd(inter: discord.Interaction):
    await _send(inter, "/bounties", fmt_bounties)

@bot.tree.command(name="roster", description="Show organization roster")
async def roster_cmd(inter: discord.Interaction):
    await _send(inter, "/roster", fmt_roster)

@bot.tree.command(name="org", description="Alias for /roster")
async def org_cmd(inter: discord.Interaction):
    await _send(inter, "/roster", fmt_roster)

@bot.tree.command(name="pirate", description="Lookup a pirate by name")
@app_commands.describe(name="Pirate name")
async def pirate_cmd(inter: discord.Interaction, name: str):
    await inter.response.defer(ephemeral=True)
    encoded = quote_plus(name)
    data, err = await http_get_json(f"/pirates/by-name?name={encoded}")
    if err:
        await inter.followup.send(f"⚠️ {err}")
        return
    try:
        msg = fmt_pirate(data, name)
    except Exception as e:
        msg = f"⚠️ Could not render pirate payload: {e}"
    await inter.followup.send(msg)

@bot.tree.command(name="pirateid", description="Lookup a pirate by player ID")
@app_commands.describe(player_id="Numeric player ID")
async def pirateid_cmd(inter: discord.Interaction, player_id: str):
    await _send(inter, f"/pirates/{player_id}", lambda d: fmt_pirate(d, player_id))

# ---------- NEW: /postevent ----------
@bot.tree.command(name="postevent", description="Record a new pirate attack event")
@app_commands.describe(
    attacker="Pirate/attacker name",
    victim="Victim name",
    zone="Nearest moon/planet (e.g., Daymar)",
    x="X coord (float)",
    y="Y coord (float)",
    z="Z coord (float)",
    attacker_org="Attacker org tag (optional)",
    victim_org="Victim org tag (optional)",
    timestamp_iso="ISO8601 (optional, default: now UTC)"
)
async def post_event(
    inter: discord.Interaction,
    attacker: str,
    victim: str,
    zone: str,
    x: float,
    y: float,
    z: float,
    attacker_org: str = "",
    victim_org: str = "",
    timestamp_iso: str = "",
):
    """Sends payload that matches EventCreate:
       { attacker_name, victim_name, attacker_org?, victim_org?, zone, coords{x,y,z}, timestamp }
    """
    await inter.response.defer(ephemeral=True)

    if not CLIENT_API_KEY:
        await inter.followup.send("⚠️ Missing CLIENT_API_KEY in bot .env — cannot post.")
        return

    if not timestamp_iso:
        timestamp_iso = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    payload = {
        "attacker_name": attacker,
        "victim_name": victim,
        "attacker_org": attacker_org or None,
        "victim_org": victim_org or None,
        "zone": zone,
        "coords": {"x": x, "y": y, "z": z},
        "timestamp": timestamp_iso
        # Optionals if your backend accepts them:
        # "weapon": "CF-337 Panther",
        # "damage_type": "Energy",
        # "ship_value_estimate": 235000,
        # "source_line": "Discord /postevent"
    }

    data, err = await http_post_json("/events", payload, use_client_key=True)
    if err:
        await inter.followup.send(f"⚠️ {err}")
        return

    # backend returns EventOut; try to show id if present
    event_id = None
    try:
        event_id = (data or {}).get("event_id") or (data or {}).get("id")
    except Exception:
        pass

    msg = f"✅ Event recorded: **{attacker}** attacked **{victim}** near **{zone}** @ ({x}, {y}, {z})"
    if event_id:
        msg += f" — id `{event_id}`"
    await inter.followup.send(msg)

# ---------- run ----------
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("Missing DISCORD_TOKEN in .env")
    try:
        bot.run(DISCORD_TOKEN)
    finally:
        if session and not session.closed:
            asyncio.get_event_loop().run_until_complete(session.close())