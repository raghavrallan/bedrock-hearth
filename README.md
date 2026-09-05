# Friends SMP — Minecraft Bedrock

Bedrock Dedicated Server in Docker on this laptop. Friends reach it over [Tailscale](https://tailscale.com), so no router port-forwarding is needed. A [playit.gg](https://playit.gg) tunnel is also defined but off by default (enable with the `playit` compose profile).

Keep this PC on and Docker Desktop running while people play.

## Daily use

```powershell
.\start.ps1
.\stop.ps1
```

## How to join

**Same Wi-Fi:** Minecraft → Play → Servers → Add Server

- Server name: `Friends SMP`
- Address: `192.168.1.4`
- Port: `19132`

**Over the internet:** the friend installs Tailscale and gets invited to this machine, then connects to the Tailscale IP on port `19132`. Full steps are in `FRIENDS.txt`.

Everyone needs a Microsoft / Xbox account (`online-mode` is on).

## Settings dashboard

http://127.0.0.1:8088

The dashboard lists every Bedrock Dedicated Server property (world, players, performance, network, anti-cheat, logging, scripts). Use the tabs or search, then **Save & apply all settings**.

The world is stored in the Docker volume `minecraft-server_mc-data` (not the `data/` folder).

## Backups

`backup-run.ps1` is the entry point; it syntax-checks `backup-daily.ps1` and runs it, so a broken script reports itself instead of failing silently. Backups go to `D:\Backup raghav\projects\friends-smp` and are kept for 14 days.

The `FriendsSMP-DailyBackup` scheduled task runs at 6:00 AM and then repeats hourly for 18 hours. Every run passes `-IfNeeded`, so the retries stop as soon as one succeeds that day. A failed 6:00 AM run therefore retries at 7:00, 8:00, and so on rather than waiting for tomorrow.

Either way you get a Windows notification, with the reason on failure. The same status shows on the dashboard, in red if the last backup failed or is more than a day stale.

```powershell
.\backup-run.ps1            # back up now
.\backup-run.ps1 -IfNeeded  # only if today's backup hasn't succeeded yet
```

## Add-ons

`addons/veinminer` is a behavior pack, bind-mounted into the container. Breaking one ore breaks the connected vein (capped per break). In the Nether it is limited to rare blocks such as ancient debris, quartz, and gilded blackstone. Note that Bedrock calls nether quartz ore `quartz_ore`, which the script normalizes.

Because it is bind-mounted, an empty `addons/veinminer` folder means the script silently does not load. The startup log should show `Pack Stack - [00] Friends SMP Vein Miner`.

`addons/xray` is a **resource pack**, so unlike the vein miner it changes rendering on the client, not the server. It replaces 76 bulk terrain textures (stone, dirt, deepslate, gravel, sand, netherrack, end stone) with transparent PNGs so ores stand out. All 21 ore textures are left alone, as are brick and tile variants so builds stay visible.

Bedrock has no per-player resource packs: installing it on the server gives it to everyone who joins. It is currently **not** installed server-side. To use it yourself only, open the dashboard on your phone and tap the download link, or install `dist/friends-smp-xray.mcpack` directly. Turn **Smooth Lighting off** afterwards or ores render black.

To change which blocks are hidden, edit `addons/xray-blocks.txt` and re-run:

```powershell
.\addons\build-xray.ps1
```

Texture names must match vanilla Bedrock filenames exactly — see [Mojang/bedrock-samples](https://github.com/Mojang/bedrock-samples/tree/main/resource_pack/textures/blocks). A wrong name fails silently, leaving the block solid. The build script refuses to run if the list contains an ore texture.
