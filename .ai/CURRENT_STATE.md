# Current State

## Working

- Docker Bedrock server + start/stop scripts
- Local dashboard for all BDS settings + power + world rules
- Daily/hourly backup with notifications and dashboard status
- Vein miner behavior pack bind-mounted into container (v1.0.8: ores + mud clear up to 50)
- X-ray resource pack build + dashboard download (not forced on all players)
- Tailscale join path documented in `FRIENDS.txt` / `PUBLIC.txt`

## Uncommitted local changes (as of 2026-09-13)

- `addons/veinminer/*` and `world_behavior_packs.json` (vein miner v1.0.3 area; owner-gated mining)
- `dashboard/app.py`
- Untracked: `dist/friends-smp-home-concept.png`

## Not present

- No `.ai/` existed before this session (now created)
- No automated tests suite in repo
