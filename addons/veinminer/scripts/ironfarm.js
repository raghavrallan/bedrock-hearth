import {
  world,
  system,
  ItemStack,
  CommandPermissionLevel,
  CustomCommandParamType,
  CustomCommandStatus,
} from "@minecraft/server";

/**
 * Bedrock spawns iron golems only while a player is inside the village
 * simulation box (about 64 x 44 blocks at tick-distance 4). A ticking area
 * keeps the chunks active once someone is in the Overworld, but it does not
 * satisfy that player check (MCPE-226025).
 *
 * This keeper:
 * - loads the farm with ticking area "ironfarm"
 * - spawns one golem on the marked platform every 35s while players are in
 *   the Overworld but outside that box, so the existing kill chamber runs
 * - while nobody is in the Overworld, records the gap and puts the iron in
 *   the farm chest when someone returns (those chunks are frozen until then)
 *
 * Owner marks the platform with /friends:ironfarm
 * (chat commands are not in script API 2.10). Backup: /scriptevent ironfarm:cmd here
 * COVER_XZ / COVER_Y follow tick-distance 4 (dashboard TICK_DISTANCE).
 */

const OWNER_TAG = "friends_owner";
const OWNER_NAMES = new Set(["busyybeeee"]);
const KEY = "ironfarm_v1";
const AREA = "ironfarm";
const GOLEM = "minecraft:iron_golem";
const KEEPER_TAG = "ironfarm_keeper";
const INGOT = "minecraft:iron_ingot";

const SIM_CHUNKS = 4;
const COVER_XZ = 8 * SIM_CHUNKS + 32;
const COVER_Y = 8 * SIM_CHUNKS + 12;
const SPAWN_TICKS = 700;
const SPAWN_MS = 35000;
const INGOTS = 4;
const STUCK_MS = 60000;
const MAX_AWAY_MS = 7 * 24 * 60 * 60 * 1000;
const CHEST_IDS = new Set([
  "minecraft:chest",
  "minecraft:trapped_chest",
  "minecraft:barrel",
]);

const born = new Map();
let nextSpawnTick = 0;
let booted = false;

function nameOf(player) {
  try {
    const n = String(player.name ?? "").trim().toLowerCase();
    if (n) return n;
  } catch {}
  try {
    return String(player.nameTag ?? "").trim().toLowerCase();
  } catch {
    return "";
  }
}

function isOwner(player) {
  if (!player) return false;
  try {
    if (player.hasTag(OWNER_TAG)) return true;
  } catch {}
  const n = nameOf(player);
  return !!(n && (OWNER_NAMES.has(n) || n.includes("busyy")));
}

function overworld() {
  return world.getDimension("overworld");
}

function isOverworld(dimension) {
  const id = String(dimension?.id || "");
  return id === "minecraft:overworld" || id === "overworld";
}

function load() {
  try {
    const raw = world.getDynamicProperty(KEY);
    if (typeof raw !== "string" || !raw) return null;
    const cfg = JSON.parse(raw);
    if (!cfg || typeof cfg !== "object") return null;
    if (!Array.isArray(cfg.chests)) cfg.chests = [];
    return cfg;
  } catch {
    return null;
  }
}

function save(cfg) {
  try {
    world.setDynamicProperty(KEY, JSON.stringify(cfg));
  } catch (e) {
    console.warn("[ironfarm] save " + e);
  }
}

function tell(player, text) {
  try {
    if (player) player.sendMessage(text);
    else world.sendMessage(text);
  } catch {}
}

function overworldPlayers() {
  const list = [];
  let players = [];
  try {
    players = world.getPlayers();
  } catch {
    return list;
  }
  for (const player of players) {
    try {
      if (isOverworld(player.dimension)) list.push(player);
    } catch {}
  }
  return list;
}

function playerCoversFarm(player, cfg) {
  try {
    const dx = player.location.x - cfg.x;
    const dy = player.location.y - cfg.y;
    const dz = player.location.z - cfg.z;
    return Math.abs(dx) <= COVER_XZ && Math.abs(dz) <= COVER_XZ && Math.abs(dy) <= COVER_Y;
  } catch {
    return false;
  }
}

function ensureArea(cfg) {
  const dim = overworld();
  const x = Math.floor(cfg.x);
  const y = Math.floor(cfg.y);
  const z = Math.floor(cfg.z);
  try {
    dim.runCommand(`tickingarea remove ${AREA}`);
  } catch {}
  const cmd = `tickingarea add circle ${x} ${y} ${z} 3 ${AREA}`;
  try {
    dim.runCommand(cmd);
    return true;
  } catch {}
  try {
    dim.runCommand("/" + cmd);
    return true;
  } catch (e) {
    console.warn("[ironfarm] tickingarea " + e);
    return false;
  }
}

function removeArea() {
  try {
    overworld().runCommand(`tickingarea remove ${AREA}`);
  } catch {}
}

function findChests(dim, x, y, z) {
  const found = [];
  const r = 10;
  const y0 = Math.max(-64, Math.floor(y) - 8);
  const y1 = Math.min(320, Math.floor(y) + 6);
  for (let dx = -r; dx <= r; dx++) {
    for (let dz = -r; dz <= r; dz++) {
      for (let yy = y0; yy <= y1; yy++) {
        let block;
        try {
          block = dim.getBlock({ x: Math.floor(x) + dx, y: yy, z: Math.floor(z) + dz });
        } catch {
          continue;
        }
        if (!block || !CHEST_IDS.has(block.typeId)) continue;
        const bx = Math.floor(block.location.x);
        const by = Math.floor(block.location.y);
        const bz = Math.floor(block.location.z);
        const dist = dx * dx + (yy - y) * (yy - y) + dz * dz;
        found.push({ x: bx, y: by, z: bz, dist });
      }
    }
  }
  found.sort((a, b) => a.dist - b.dist);
  const uniq = [];
  const seen = new Set();
  for (const chest of found) {
    const key = `${chest.x}|${chest.y}|${chest.z}`;
    if (seen.has(key)) continue;
    seen.add(key);
    uniq.push({ x: chest.x, y: chest.y, z: chest.z });
    if (uniq.length >= 6) break;
  }
  return uniq;
}

function viewedBlock(player) {
  try {
    const hit = player.getBlockFromViewDirection({ maxDistance: 8 });
    if (!hit) return null;
    if (hit.typeId) return hit;
    if (hit.block) return hit.block;
  } catch {}
  return null;
}

function insertIron(container, count) {
  let left = count;
  const size = container.size;
  for (let i = 0; i < size && left > 0; i++) {
    const stack = container.getItem(i);
    if (!stack || stack.typeId !== INGOT) continue;
    const max = stack.maxAmount || 64;
    if (stack.amount >= max) continue;
    const add = Math.min(left, max - stack.amount);
    container.setItem(i, new ItemStack(INGOT, stack.amount + add));
    left -= add;
  }
  for (let i = 0; i < size && left > 0; i++) {
    if (container.getItem(i)) continue;
    const add = Math.min(left, 64);
    container.setItem(i, new ItemStack(INGOT, add));
    left -= add;
  }
  return left;
}

function flush(cfg) {
  const pending = cfg.pending || 0;
  if (pending <= 0) return 0;
  const dim = overworld();
  let left = pending;
  for (const chest of cfg.chests || []) {
    let block;
    try {
      block = dim.getBlock({ x: chest.x, y: chest.y, z: chest.z });
    } catch {
      continue;
    }
    const container = block?.getComponent("minecraft:inventory")?.container;
    if (!container) continue;
    try {
      left = insertIron(container, left);
    } catch {
      continue;
    }
    if (left <= 0) break;
  }
  cfg.pending = left;
  if (left !== pending) save(cfg);
  return pending - left;
}

function keeperGolems(dim, cfg) {
  try {
    const list = dim.getEntities({
      type: GOLEM,
      location: { x: cfg.x, y: cfg.y, z: cfg.z },
      maxDistance: 48,
    });
    return list.filter((ent) => {
      try {
        return ent.hasTag(KEEPER_TAG);
      } catch {
        return false;
      }
    });
  } catch {
    return [];
  }
}

function sweep(dim, cfg) {
  const list = keeperGolems(dim, cfg);
  const live = new Set();
  const now = Date.now();
  for (const ent of list) {
    let id = "";
    try {
      id = ent.id;
    } catch {
      continue;
    }
    live.add(id);
    let age = born.get(id) || 0;
    if (!age) {
      try {
        const stored = ent.getDynamicProperty("ironfarm_born");
        if (typeof stored === "number") age = stored;
      } catch {}
    }
    if (!age) {
      born.set(id, now);
      try {
        ent.setDynamicProperty("ironfarm_born", now);
      } catch {}
      continue;
    }
    if (now - age < STUCK_MS) continue;
    let x = cfg.x;
    let y = cfg.y;
    let z = cfg.z;
    try {
      x = ent.location.x;
      y = ent.location.y;
      z = ent.location.z;
    } catch {}
    const xi = Math.floor(x);
    const yi = Math.floor(y);
    const zi = Math.floor(z);
    try {
      dim.runCommand(
        `kill @e[type=iron_golem,tag=${KEEPER_TAG},x=${xi},y=${yi},z=${zi},r=3,c=1]`
      );
    } catch {
      try {
        ent.kill();
      } catch {}
    }
    born.delete(id);
  }
  for (const id of born.keys()) {
    if (!live.has(id)) born.delete(id);
  }
}

function trySpawn(dim, cfg) {
  if (keeperGolems(dim, cfg).length) return;
  const pos = { x: cfg.x, y: cfg.y, z: cfg.z };
  try {
    const ent = dim.spawnEntity(GOLEM, pos);
    const now = Date.now();
    try {
      ent.addTag(KEEPER_TAG);
    } catch {}
    try {
      ent.setDynamicProperty("ironfarm_born", now);
    } catch {}
    try {
      born.set(ent.id, now);
    } catch {}
  } catch (e) {
    console.warn("[ironfarm] spawn failed " + e);
    ensureArea(cfg);
    cfg.pending = (cfg.pending || 0) + INGOTS;
    save(cfg);
  }
}

function syncPresence() {
  const cfg = load();
  if (!cfg?.enabled) return;
  const present = overworldPlayers().length > 0;
  if (!present) {
    if (!cfg.emptySince) {
      cfg.emptySince = Date.now();
      save(cfg);
    }
    return;
  }
  if (!cfg.emptySince) {
    flush(cfg);
    return;
  }
  let elapsed = Date.now() - cfg.emptySince;
  let capped = false;
  if (elapsed > MAX_AWAY_MS) {
    elapsed = MAX_AWAY_MS;
    capped = true;
  }
  if (elapsed < 0) elapsed = 0;
  cfg.emptySince = 0;
  const ingots = Math.floor(elapsed / SPAWN_MS) * INGOTS;
  cfg.pending = (cfg.pending || 0) + ingots;
  save(cfg);
  const inserted = flush(load() || cfg);
  if (ingots <= 0) return;
  const pending = (load() || cfg).pending || 0;
  let msg = `Iron farm caught up: ${ingots} iron for the time the Overworld was empty.`;
  if (pending > 0) {
    msg += ` ${inserted} fit in the chest. Empty it — ${pending} more will flow in.`;
  }
  if (capped) msg += " Catch-up is capped at 7 days.";
  tell(null, msg);
}

function tick() {
  const cfg = load();
  if (!cfg?.enabled) return;
  syncPresence();
  const fresh = load();
  if (!fresh?.enabled) return;
  if (!overworldPlayers().length) return;
  const dim = overworld();
  flush(fresh);
  sweep(dim, fresh);
  if (overworldPlayers().some((player) => playerCoversFarm(player, fresh))) return;
  if (system.currentTick < nextSpawnTick) return;
  nextSpawnTick = system.currentTick + SPAWN_TICKS;
  trySpawn(dim, load() || fresh);
}

function setupHere(player) {
  const loc = player.location;
  const dim = player.dimension;
  const chests = findChests(dim, loc.x, loc.y, loc.z);
  const prev = load();
  const cfg = {
    enabled: true,
    x: loc.x,
    y: loc.y,
    z: loc.z,
    chests,
    emptySince: 0,
    pending: prev?.pending || 0,
  };
  save(cfg);
  const areaOk = ensureArea(cfg);
  const x = Math.floor(loc.x);
  const y = Math.floor(loc.y);
  const z = Math.floor(loc.z);
  let msg =
    `Iron farm keeper on at ${x} ${y} ${z}. ` +
    "It keeps running when you walk away. " +
    "While someone is in the Overworld, golems spawn on this spot about every 35 seconds. " +
    "While the Overworld is empty, iron is stored and added to the farm chest when someone comes back.";
  if (!chests.length) {
    msg += " No chest within 10 blocks — look at the output chest and run /friends:ironfarm chest.";
  } else {
    msg += ` Output chest at ${chests[0].x} ${chests[0].y} ${chests[0].z}.`;
  }
  if (!areaOk) msg += " Ticking area command failed — cheats need to stay on.";
  tell(player, msg);
}

function addChest(player) {
  const cfg = load();
  if (!cfg?.enabled) {
    tell(player, "Stand on the golem spawn spot and run /friends:ironfarm first.");
    return;
  }
  const block = viewedBlock(player);
  if (!block || !CHEST_IDS.has(block.typeId)) {
    tell(player, "Look at a chest or barrel (within 8 blocks) and run /friends:ironfarm chest.");
    return;
  }
  const chest = {
    x: Math.floor(block.location.x),
    y: Math.floor(block.location.y),
    z: Math.floor(block.location.z),
  };
  const key = `${chest.x}|${chest.y}|${chest.z}`;
  const chests = Array.isArray(cfg.chests) ? cfg.chests.slice() : [];
  if (!chests.some((c) => `${c.x}|${c.y}|${c.z}` === key)) chests.unshift(chest);
  cfg.chests = chests.slice(0, 8);
  save(cfg);
  tell(player, `Iron farm output chest set to ${chest.x} ${chest.y} ${chest.z}.`);
}

function showStatus(player) {
  const cfg = load();
  if (!cfg?.enabled) {
    tell(player, "Iron farm keeper is off. Stand in the golem water and run /friends:ironfarm.");
    return;
  }
  const away = cfg.emptySince ? "Overworld empty — catch-up is recording." : "Overworld active.";
  tell(
    player,
    `Iron farm keeper on at ${Math.floor(cfg.x)} ${Math.floor(cfg.y)} ${Math.floor(cfg.z)}. ` +
      `Chests: ${(cfg.chests || []).length}. Waiting iron: ${cfg.pending || 0}. ${away}`
  );
}

function turnOff(player) {
  const cfg = load() || {};
  cfg.enabled = false;
  cfg.emptySince = 0;
  save(cfg);
  removeArea();
  tell(player, "Iron farm keeper off. The farm runs only while you are next to it again. Run /friends:ironfarm to turn it back on.");
}

function handleChat(player, message) {
  if (!isOwner(player)) {
    tell(player, "Only the server owner can set the iron farm keeper.");
    return;
  }
  try {
    player.addTag(OWNER_TAG);
  } catch {}
  const parts = String(message || "")
    .trim()
    .toLowerCase()
    .split(/\s+/);
  if (parts[0] !== "!ironfarm") return;
  const sub = parts[1] || "";
  if (sub === "status") {
    showStatus(player);
    return;
  }
  if (sub === "off") {
    turnOff(player);
    return;
  }
  if (!isOverworld(player.dimension)) {
    tell(player, "Set the iron farm keeper from the Overworld.");
    return;
  }
  if (sub === "chest") addChest(player);
  else if (sub === "on") {
    const cfg = load();
    if (!cfg || typeof cfg.x !== "number") setupHere(player);
    else {
      cfg.enabled = true;
      cfg.emptySince = 0;
      save(cfg);
      ensureArea(cfg);
      tell(player, "Iron farm keeper back on at the saved spot.");
    }
  } else if (!sub || sub === "here") setupHere(player);
  else tell(player, "Use /friends:ironfarm, /friends:ironfarm chest, /friends:ironfarm status, or /friends:ironfarm off.");
}

function scheduleSync() {
  system.runTimeout(() => {
    try {
      syncPresence();
    } catch (e) {
      console.warn("[ironfarm] sync " + e);
    }
  }, 5);
}

function onOwnerSpawn(player) {
  if (!isOwner(player)) return;
  try {
    player.addTag(OWNER_TAG);
  } catch {}
  const cfg = load();
  if (cfg?.enabled) {
    ensureArea(cfg);
    return;
  }
  tell(
    player,
    "Iron farm pauses when you leave it. Stand in the golem spawn water and run /friends:ironfarm so it keeps producing."
  );
}

function boot(attempt) {
  system.runTimeout(() => {
    try {
      const cfg = load();
      if (!cfg?.enabled) {
        console.warn("[ironfarm] v1.0.26 waiting for /friends:ironfarm");
        booted = true;
        return;
      }
      const ok = ensureArea(cfg);
      if (!ok && attempt < 5) {
        boot(attempt + 1);
        return;
      }
      if (!overworldPlayers().length) {
        cfg.emptySince = Date.now();
      } else {
        cfg.emptySince = 0;
      }
      save(cfg);
      booted = true;
      console.warn("[ironfarm] v1.0.26 keeper on");
    } catch (e) {
      console.warn("[ironfarm] boot " + e);
      if (attempt < 5) boot(attempt + 1);
    }
  }, attempt === 0 ? 100 : 200);
}

function runFarmCommand(player, action) {
  if (!player || player.typeId !== "minecraft:player") return;
  const sub = String(action || "here").trim().toLowerCase();
  handleChat(player, "!ironfarm" + (sub === "here" ? "" : " " + sub));
}

function register() {
  try {
    system.beforeEvents.startup.subscribe((init) => {
      try {
        const reg = init.customCommandRegistry;
        reg.registerEnum("friends:ironfarm_action", ["here", "chest", "status", "off", "on"]);
        reg.registerCommand(
          {
            name: "friends:ironfarm",
            description: "Keep the iron farm producing while you are away",
            permissionLevel: CommandPermissionLevel.Any,
            cheatsRequired: false,
            optionalParameters: [
              { name: "friends:ironfarm_action", type: CustomCommandParamType.Enum },
            ],
          },
          (origin, action) => {
            const player = origin?.sourceEntity;
            system.run(() => {
              try {
                runFarmCommand(player, action);
              } catch (e) {
                console.warn("[ironfarm] command " + e);
              }
            });
            return { status: CustomCommandStatus.Success };
          }
        );
        console.warn("[ironfarm] /friends:ironfarm registered");
      } catch (e) {
        console.warn("[ironfarm] command register " + e);
      }
    });
  } catch (e) {
    console.warn("[ironfarm] startup " + e);
  }

  try {
    system.afterEvents.scriptEventReceive.subscribe((event) => {
      if (event.id !== "ironfarm:cmd") return;
      const player = event.sourceEntity;
      const action = event.message;
      system.run(() => {
        try {
          runFarmCommand(player, action);
        } catch (e) {
          console.warn("[ironfarm] scriptevent " + e);
        }
      });
    });
  } catch (e) {
    console.warn("[ironfarm] scriptevent " + e);
  }

  if (world.afterEvents.playerSpawn) {
    world.afterEvents.playerSpawn.subscribe((event) => {
      system.run(() => {
        try {
          onOwnerSpawn(event.player);
          scheduleSync();
        } catch (e) {
          console.warn("[ironfarm] spawn " + e);
        }
      });
    });
  }
  if (world.afterEvents.playerLeave) {
    world.afterEvents.playerLeave.subscribe(() => scheduleSync());
  }
  if (world.afterEvents.playerDimensionChange) {
    world.afterEvents.playerDimensionChange.subscribe(() => scheduleSync());
  }

  system.runInterval(() => {
    try {
      tick();
    } catch (e) {
      console.warn("[ironfarm] tick " + e);
    }
  }, 20);

  if (!booted) boot(0);
}

register();
