# Pirate Bounty Tracker (Backend + Client + Discord Bot)

Org-wide piracy tracker for Star Citizen with shared backend, heatmap, roster fetch, and Discord bot.

## Deploy on Render (Free)
1) **Create GitHub repo** and push this folder (steps below).
2) In Render: **New → Blueprint** → select your repo → confirm `render.yaml`.
3) When prompted, set env vars on the web service:
   - `CLIENT_API_KEY` (e.g., `secret-client-key`)
   - `ADMIN_API_KEY` (e.g., `secret-admin-key`)
   - `DATABASE_URL` (auto-wired from the Postgres resource in the blueprint)
4) Click **Apply**. After deploy, copy your service URL.
5) Update `client/.env` and `discord-bot/.env` with `BACKEND_URL=https://<your-service>.onrender.com` and your keys.

## Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: pirate bounty tracker full stack"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

## Local Dev (optional)
Backend:
```bash
cd backend
pip install -r requirements.txt
cp .env.sample .env  # set keys if needed
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```
Client Watcher:
```bash
cd client/pirate_watcher
pip install -r requirements.txt
cp .env.sample .env
python -m pirate_watcher --log "C:\\Path\\To\\StarCitizen\\Live\\Logs\\Game.log"
```
Discord Bot:
```bash
cd discord-bot
pip install -r requirements.txt
cp .env.sample .env   # set DISCORD_TOKEN + BACKEND_URL
python bot.py
```

## Notes
- Heatmap bodies in `backend/routers/heatmap.py` are placeholders; replace with accurate coordinates.
- Parser handles attacker org as `Name (ORG) [id]`; tweak `client/pirate_watcher/parser.py` if your logs differ.
