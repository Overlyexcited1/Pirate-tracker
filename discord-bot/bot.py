import os, requests
import discord
from discord import app_commands
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
BACKEND_URL = os.getenv('BACKEND_URL','http://127.0.0.1:8000')
intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@tree.command(name='bounties', description='Show top pirates (by score)')
async def bounties(interaction: discord.Interaction):
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/bounties", timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            await interaction.response.send_message('No bounties yet.'); return
        lines = [f"**{i+1}. {p['name']}** ({p.get('org','n/a')}) — score {p['score']:.2f} | attacks {p['total_attacks']} | kills {p['total_kills']}" for i,p in enumerate(data)]
        await interaction.response.send_message('\n'.join(lines[:10]))
    except Exception as e:
        await interaction.response.send_message(f'Error: {e}')

@tree.command(name='hotspots', description='Show hotspot bodies where attacks clustered')
async def hotspots(interaction: discord.Interaction):
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/heatmap", timeout=10)
        r.raise_for_status()
        data = r.json()
        h = data.get('hotspots', [])
        if not h: await interaction.response.send_message('No hotspots recorded yet.'); return
        lines = []
        for entry in h[:8]:
            coord = entry.get('sample_coord')
            coord_str = f"({coord[0]:.1f}, {coord[1]:.1f}, {coord[2]:.1f})" if coord else 'n/a'
            lines.append(f"**{entry['body']}** — {entry['count']} events near {coord_str}")
        await interaction.response.send_message('\n'.join(lines))
    except Exception as e:
        await interaction.response.send_message(f'Error: {e}')

@tree.command(name='pirate', description='Get pirate profile by name')
@app_commands.describe(name='In-game player name')
async def pirate(interaction: discord.Interaction, name: str):
    try:
        r = requests.get(f"{BACKEND_URL}/api/v1/pirates/by-name", params={'name': name}, timeout=10)
        if r.status_code == 404: await interaction.response.send_message('No such pirate.'); return
        r.raise_for_status()
        p = r.json()
        msg = f"**{p['name']}** ({p.get('org','n/a')})\nAttacks: {p['total_attacks']}\nKills: {p['total_kills']}\nValue: {p['value_destroyed']:.0f}\nScore: {p['score']:.2f}"
        await interaction.response.send_message(msg)
    except Exception as e:
        await interaction.response.send_message(f'Error: {e}')

@bot.event
async def on_ready():
    try: await tree.sync()
    except Exception as e: print('sync err', e)
    print('Bot ready')

bot.run(TOKEN)
