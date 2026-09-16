# Agents Guide — Friends SMP

## What this is

Personal Minecraft Bedrock Dedicated Server for friends, run via Docker on a Windows laptop. Remote join is via Tailscale (primary); playit.gg is optional.

## Before changing anything

1. Read `.ai/PROJECT_CONTEXT.md` and `.ai/CURRENT_STATE.md`.
2. Prefer editing existing scripts/dashboard rather than adding new stacks.
3. Do not commit `.env` (secrets / live server config). Use `.env.example` for templates.
4. World data lives in Docker volume `minecraft-server_mc-data`, not a `data/` folder in the repo.

## Safe commands

- Start: `.\start.ps1` (bedrock + dashboard :8088 + opportunistic backup)
- Stop: `.\stop.ps1`
- Backup now: `.\backup-run.ps1`
- Rebuild xray pack: `.\addons\build-xray.ps1`

## Touch carefully

- `addons/veinminer` is bind-mounted read-only into the container. Empty folder = pack silently missing.
- Vein miner is currently **owner-only** (`busyybeeee` / tag `friends_owner`).
- X-ray is a **client resource pack**, not installed server-wide by default.
- Avoid IPv6 join addresses (documented as crash/freeze).

## Context files

Keep `.ai/*` updated after significant work. Repo code is source of truth over stale docs.
