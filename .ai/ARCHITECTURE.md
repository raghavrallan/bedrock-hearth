# Architecture

## Data flow

```
Players (LAN 192.168.1.4 / Tailscale 100.x)
    │ UDP 19132
    ▼
Docker: friends-smp (itzg BDS)
    ├── volume: minecraft-server_mc-data → /data (world + properties)
    └── bind: ./addons/veinminer → /data/behavior_packs/friends_smp_veinminer:ro

Host: dashboard/app.py :8088
    ├── reads/writes .env
    ├── docker compose / docker inspect / docker logs / attach commands
    ├── backup status from D:\Backup raghav\projects\friends-smp\last-backup.json
    └── serves dist/friends-smp-xray.mcpack at /xray.mcpack

Host: backup-run.ps1 → backup-daily.ps1
    └── archives world from container/volume → D:\Backup...\ (14-day retention)
```

## Compose services

- **bedrock** (`friends-smp`): always on with `start.ps1`; fixed IP `172.20.0.10` on `mcnet`; 4 GiB mem limit; 60 s stop grace.
- **playit**: profile `playit` only; shares `mcnet` at `172.20.0.11`. Host may also use installed `playit.exe` from `start.ps1`.

## Dashboard APIs

| Method | Path | Role |
|--------|------|------|
| GET | `/` | UI (`index.html`) |
| GET | `/api/schema` | Field definitions |
| GET | `/api/status` | Container, settings, rules, joins, backup, join IPs, logs |
| GET | `/xray.mcpack` | Download xray pack |
| POST | `/api/settings` | Validate, write `.env`, restart world |
| POST | `/api/power` | start/stop/restart container |
| POST | `/api/rules` | World rules (coords, day mode, join announce, etc.) |

## Add-ons

- **Vein miner**: `@minecraft/server` script; BFS adjacent ores; max 64; sneak = single block; Nether limited to rare ores; quartz id normalized. Enabled via `addons/world_behavior_packs.json` pack id matching manifest UUID.
- **X-ray**: transparent terrain textures; ores untouched; client-only; build from `xray-blocks.txt`.
