# Decisions

1. **Docker volume for world** — World lives in external volume `minecraft-server_mc-data`, not repo `data/`, so code/addons can change without risking world files in git.
2. **Tailscale over port-forward** — Friends join via Tailscale IP; avoids router config. playit.gg kept optional.
3. **itzg Bedrock image** — Env vars map to `server.properties`; `ENABLE_BDS_V6BIND_FIX` enabled.
4. **Python stdlib dashboard** — No Flask/FastAPI; simple local control panel on 8088.
5. **Vein miner server-side; xray client-side** — Behavior pack for mining logic; resource pack only for personal xray (Bedrock has no per-player server resource packs).
6. **Backup wrapper** — `backup-run.ps1` syntax-checks `backup-daily.ps1` before running; scheduled `-IfNeeded` retries until one success per day.
7. **Avoid IPv6 join** — Documented as causing client crash/freeze; prefer IPv4 LAN/Tailscale.
8. **Vein miner owner-only** — Script gates on name `busyybeeee` or tag `friends_owner` (current code).
9. **Iron farm keeper** — Bedrock golem spawning requires a player inside the village simulation box, so `/tickingarea` alone does not keep the farm producing. Pack script keeps ticking area `ironfarm`, spawns golems on the marked platform while anyone is in the Overworld outside that box, and catch-up deposits iron into the farm chest for time the Overworld had no players. Owner marks it with `/friends:ironfarm` (script API 2.10 has no chat event). Away credit does not include time the server process was stopped.
