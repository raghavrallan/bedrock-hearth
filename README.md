# Bedrock Hearth

A private Minecraft Bedrock world that stays on a Windows PC, so a few friends can play without renting a host or opening a router port.

Friends on the same Wi-Fi join the PC directly. Friends anywhere else join through [Tailscale](https://tailscale.com). A local dashboard turns the usual server settings into a form. Start, stop, and backup are PowerShell scripts.

This is the setup behind one real friends world. Copy it, change the server name, and run your own.

## What you get

- Bedrock Dedicated Server in Docker ([itzg/minecraft-bedrock-server](https://github.com/itzg/docker-minecraft-bedrock-server))
- A settings dashboard at `http://127.0.0.1:8088` for server properties, power, and a few world rules
- `start.ps1` / `stop.ps1`, plus a daily backup that retries and raises a Windows notification
- A vein-miner behavior pack (owner-only until you edit the name list)
- An iron-farm keeper so a Bedrock iron farm keeps producing when you walk away or log off
- An optional x-ray resource pack you install on your own game, not on every player
- An optional [playit.gg](https://playit.gg) tunnel, off unless you turn that compose profile on

## What you need

- Windows 10 or 11, with this PC awake while people play
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- A Microsoft / Xbox account for each player (`online-mode` is on)
- [Tailscale](https://tailscale.com) on this PC and on a friend's device, if they are not on your Wi-Fi

## Quick start

```powershell
git clone https://github.com/raghavrallan/bedrock-hearth.git
cd bedrock-hearth
copy .env.example .env
docker volume create minecraft-server_mc-data
.\start.ps1
```

The world is not in this folder. It lives in the Docker volume `minecraft-server_mc-data`, so pulling new code does not wipe the world. `.env` is gitignored. Put the live server name, difficulty, and any tunnel secret there.

Open the dashboard at http://127.0.0.1:8088, then **Save & apply all settings** after you change them.

Stop the world with `.\stop.ps1`.

## How friends join

In Minecraft: **Play → Servers → Add Server**. Port **19132**.

Use an IPv4 address. An IPv6 address can freeze or crash the Bedrock client.

**Same Wi-Fi.** Use this PC's LAN IPv4. `start.ps1` prints the address it finds. `FRIENDS.txt` is a fill-in card for the addresses you actually give people.

**From anywhere else.** Install Tailscale on this PC and on their phone or computer. Sign them into your tailnet (or share this machine with their email from the [Tailscale admin page](https://login.tailscale.com/admin/machines)). They add a server whose address is this PC's Tailscale IPv4 (`100.x.x.x`), still on port `19132`.

Everyone needs a Microsoft / Xbox account.

## Iron farm

Bedrock only starts iron-golem spawns while a player is within about 64 blocks of the village. Walking away or logging off stops a normal farm even when the chunks are still loaded.

After the server is up, stand in the water where golems should spawn and run:

```
/friends:ironfarm
```

That marks the spot, keeps those chunks loaded, and uses the nearest chest or barrel as the output. Look at a different chest and run `/friends:ironfarm chest` if the collection chest is farther away.

- Someone is in the Overworld, but not next to the farm: a golem is placed on that spot about every 35 seconds, and the farm's lava and hoppers collect the drops.
- Nobody is in the Overworld: the game freezes those chunks. The keeper records the gap and puts the iron in the chest when someone comes back (about 4 ingots per 35 seconds). Empty the chest if it fills; the rest waits.
- You are standing at the farm: the normal farm runs, and the keeper stays quiet.

`/friends:ironfarm status` and `/friends:ironfarm off` do what they say. The PC and Docker have to stay on. If the machine sleeps, the world pauses with it.

## Other add-ons

**Vein miner** (`addons/veinminer`) is mounted into the server. Breaking one ore breaks the connected vein, up to a cap. Sneak-mining breaks a single block. It currently answers only to the owner name in `addons/veinminer/scripts/main.js` and `scripts/ironfarm.js` (`busyybeeee`, or the tag `friends_owner`). Change `OWNER_NAMES` if this is your world.

The startup log should include `Pack Stack - [00] Friends SMP Vein Miner`. An empty `addons/veinminer` folder means the pack never loads.

**X-ray** (`addons/xray`) is a client resource pack. It makes bulk terrain see-through and leaves ores alone. It is not forced on everyone who joins. Download it from the dashboard, or install `dist/friends-smp-xray.mcpack` on your own game. Turn Smooth Lighting off or the hidden blocks render black.

To change which blocks are hidden, edit `addons/xray-blocks.txt` and run `.\addons\build-xray.ps1`. Names must match vanilla Bedrock texture filenames. The build refuses to run if the list contains an ore.

## Backups

`.\backup-run.ps1` checks `backup-daily.ps1` and then runs it. `.\backup-run.ps1 -IfNeeded` does nothing if today's backup already succeeded.

On this PC the files go to `D:\Backup raghav\projects\friends-smp` and are kept for 14 days. Before you trust that on another machine, point these three lines at a folder you have:

- `backup-daily.ps1` and `backup-run.ps1` (`$BackupRoot`)
- `dashboard/app.py` (`BACKUP_META`)

A scheduled task can call `backup-run.ps1 -IfNeeded` every hour. The dashboard shows whether the last backup worked.

## Make it yours

| Change | Where |
| --- | --- |
| Server name, game mode, view distance | `.env` (start from `.env.example`) |
| Who vein miner and the iron-farm command answer to | `OWNER_NAMES` in the two scripts under `addons/veinminer/scripts/` |
| Backup folder | The three paths listed above |
| Join card you hand to friends | `FRIENDS.txt` |

Do not commit `.env`. It holds the live settings and any tunnel secret.

## Layout

```
docker-compose.yml     bedrock container, optional playit profile
.env.example           settings template
start.ps1 / stop.ps1
backup-run.ps1         backup entry point
dashboard/             settings UI on port 8088
addons/veinminer/      vein miner + iron farm keeper
addons/xray/           optional client resource pack
```

## License

[MIT](LICENSE). Use it, change it, and run your own world.
