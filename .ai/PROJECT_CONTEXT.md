# Project Context

## Purpose

Run a private **Friends SMP** Minecraft Bedrock world on this PC so friends can join over LAN or Tailscale without port-forwarding.

## Stack

| Piece | Tech |
|--------|------|
| Server | `itzg/minecraft-bedrock-server` (Docker Compose) |
| Config | `.env` → BDS `server.properties` via itzg image |
| Control UI | Python `ThreadingHTTPServer` (`dashboard/app.py`) on `:8088` |
| Ops scripts | PowerShell (`start.ps1`, `stop.ps1`, backups, notify) |
| Remote access | Tailscale (primary); playit.gg (optional profile / local agent) |
| Add-ons | Bedrock behavior pack (vein miner) + optional resource pack (xray) |

## Layout

```
minecraft-server/
  docker-compose.yml      # bedrock + optional playit
  .env / .env.example     # live / template server settings
  start.ps1 / stop.ps1
  backup-*.ps1, notify.ps1
  FRIENDS.txt / PUBLIC.txt  # join instructions
  dashboard/                # settings UI + APIs
  addons/veinminer/         # scripted behavior pack (server)
  addons/xray/ + build-xray.ps1
  dist/                     # built .mcpack, assets
```

## Runtime requirements

- Docker Desktop running
- PC on; Tailscale connected for remote friends
- Microsoft/Xbox accounts (`ONLINE_MODE=true`)
