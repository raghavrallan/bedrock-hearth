# Session

## 2026-09-27 — Iron farm runs while away

- Bedrock will not spawn iron golems from a ticking area alone (MCPE-226025). Keeper added in vein miner pack v1.0.25.
- Owner stands on the golem spawn spot and runs `/friends:ironfarm`. Output chest is the nearest chest/barrel, or `/friends:ironfarm chest`. Backup if the slash command is missing: `/scriptevent ironfarm:cmd here`.
- Overworld occupied but player outside ~64×44 of the mark: script spawns a golem every 35s into the existing farm.
- Overworld empty (offline, Nether, End): gap is recorded and iron is inserted into the chest on return. Server process must stay up; a restart does not pay the gap from before boot.

## 2026-09-13 — Xray RP fails on client (black boxes)

- Server-forced xray resource pack removed (`world_resource_packs.json` = `[]`, `TEXTUREPACK_REQUIRED=false`, compose mount removed).
- Root cause: Bedrock paints alpha=0 on opaque blocks as **black**, not see-through (worse with Smooth Lighting / Vibrant Visuals). Neon borders proved pack loaded; centers were black voids.
- Owner workaround: chat `!xray` toggles **spectator** (real see-through), `!xray` again returns to survival + god mode. Vein miner pack v1.0.5.

- Gave busyybeeee iron armor, steak, cobblestone.
- Enabled god mode (friends_god + resistance/regen/fire_res/saturation/absorption/health_boost).
- Vein miner pack now *applies* god mode for owner on spawn (was clearing legacy god); bumped to 1.0.4; server restarted; pack loaded.

## Earlier — Understand project

- Created `AGENTS.md` and `.ai/*` context.
