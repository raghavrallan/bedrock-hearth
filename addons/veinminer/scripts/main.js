import { world, system } from "@minecraft/server";

const OWNER_TAG = "friends_owner";
const OWNER_NAMES = new Set(["busyybeeee"]);

const VEIN_BLOCKS = new Set([
  "minecraft:gold_ore",
  "minecraft:deepslate_gold_ore",
  "minecraft:iron_ore",
  "minecraft:deepslate_iron_ore",
  "minecraft:copper_ore",
  "minecraft:deepslate_copper_ore",
  "minecraft:diamond_ore",
  "minecraft:deepslate_diamond_ore",
  "minecraft:coal_ore",
  "minecraft:deepslate_coal_ore",
  "minecraft:redstone_ore",
  "minecraft:lit_redstone_ore",
  "minecraft:deepslate_redstone_ore",
  "minecraft:lapis_ore",
  "minecraft:deepslate_lapis_ore",
  "minecraft:emerald_ore",
  "minecraft:deepslate_emerald_ore",
  "minecraft:obsidian",
  "minecraft:crying_obsidian",
  "minecraft:calcite",
  "minecraft:amethyst_block",
  "minecraft:budding_amethyst",
  "minecraft:amethyst_cluster",
  "minecraft:large_amethyst_bud",
  "minecraft:medium_amethyst_bud",
  "minecraft:small_amethyst_bud",
  "minecraft:nether_gold_ore",
  "minecraft:quartz_ore",
  "minecraft:nether_quartz_ore",
  "minecraft:ancient_debris",
  "minecraft:gilded_blackstone",
]);

const QUARTZ_ORES = new Set([
  "minecraft:quartz_ore",
  "minecraft:nether_quartz_ore",
]);

const AMETHYST = new Set([
  "minecraft:amethyst_cluster",
  "minecraft:large_amethyst_bud",
  "minecraft:medium_amethyst_bud",
  "minecraft:small_amethyst_bud",
]);

const MAX_VEIN = 64;
const DIRS = [
  [1, 0, 0],
  [-1, 0, 0],
  [0, 1, 0],
  [0, -1, 0],
  [0, 0, 1],
  [0, 0, -1],
];

let registered = false;

function nameOf(p) {
  try {
    const n = String(p.name ?? "").trim().toLowerCase();
    if (n) return n;
  } catch {}
  try {
    return String(p.nameTag ?? "").trim().toLowerCase();
  } catch {
    return "";
  }
}

function isOwner(p) {
  if (!p) return false;
  try {
    if (p.hasTag(OWNER_TAG)) return true;
  } catch {}
  const n = nameOf(p);
  return !!(n && (OWNER_NAMES.has(n) || n.includes("busyy")));
}

function markOwner(p) {
  if (!isOwner(p)) return;
  try {
    p.addTag(OWNER_TAG);
  } catch {}
}

function posKey(x, y, z) {
  return `${x}|${y}|${z}`;
}

/** Break with drops — never setType(air) (that deletes items). */
function breakWithDrops(dim, x, y, z) {
  const xi = Math.floor(x);
  const yi = Math.floor(y);
  const zi = Math.floor(z);
  try {
    dim.runCommand(`setblock ${xi} ${yi} ${zi} air destroy`);
    return true;
  } catch {}
  try {
    // Fallback: still prefer destroy-style if available
    dim.runCommand(`/setblock ${xi} ${yi} ${zi} air destroy`);
    return true;
  } catch {
    return false;
  }
}

function sameVein(block, typeId) {
  if (!block) return false;
  const id = block.typeId;
  if (id === typeId) return true;
  if (QUARTZ_ORES.has(id) && QUARTZ_ORES.has(typeId)) return true;
  if (AMETHYST.has(id) && AMETHYST.has(typeId)) return true;
  return false;
}

function veinMine(dim, sx, sy, sz, typeId) {
  const q = [{ x: sx, y: sy, z: sz }];
  const seen = new Set([posKey(sx, sy, sz)]);
  const extra = [];
  while (q.length && extra.length < MAX_VEIN) {
    const c = q.shift();
    for (const [dx, dy, dz] of DIRS) {
      const x = c.x + dx;
      const y = c.y + dy;
      const z = c.z + dz;
      const k = posKey(x, y, z);
      if (seen.has(k)) continue;
      seen.add(k);
      let b;
      try {
        b = dim.getBlock({ x, y, z });
      } catch {
        continue;
      }
      if (!sameVein(b, typeId)) continue;
      extra.push({ x, y, z });
      q.push({ x, y, z });
    }
  }
  for (const p of extra) breakWithDrops(dim, p.x, p.y, p.z);
}

function normalizeOre(id) {
  if (QUARTZ_ORES.has(id)) return "minecraft:quartz_ore";
  if (AMETHYST.has(id)) return "minecraft:amethyst_cluster";
  return id;
}

function handleBreak(player, typeId, x, y, z) {
  if (!isOwner(player)) return;
  markOwner(player);
  if (!typeId) return;

  try {
    if (player.isSneaking) return;
  } catch {}

  let oreId = normalizeOre(typeId);
  if (!VEIN_BLOCKS.has(oreId) && !VEIN_BLOCKS.has(typeId)) return;
  if (!VEIN_BLOCKS.has(oreId)) oreId = typeId;

  const sx = Math.floor(x);
  const sy = Math.floor(y);
  const sz = Math.floor(z);
  const dim = player.dimension;

  system.run(() => veinMine(dim, sx, sy, sz, oreId));
}

function onBreakBefore(event) {
  try {
    const player = event.player;
    if (!isOwner(player)) return;
    const block = event.block;
    const typeId = block?.typeId || "";
    const loc = block.location;
    system.run(() => handleBreak(player, typeId, loc.x, loc.y, loc.z));
  } catch (e) {
    try {
      console.warn("[veinminer] beforeBreak: " + e);
    } catch {}
  }
}

function onBreakAfter(event) {
  try {
    if (world.beforeEvents?.playerBreakBlock) return;
    const player = event.player;
    if (!isOwner(player)) return;
    let typeId = "";
    try {
      typeId = event.brokenBlockPermutation?.type?.id || "";
    } catch {}
    if (!typeId) {
      try {
        typeId = event.brokenBlockPermutation?.typeId || "";
      } catch {}
    }
    const loc = event.block.location;
    handleBreak(player, typeId, loc.x, loc.y, loc.z);
  } catch (e) {
    try {
      console.warn("[veinminer] afterBreak: " + e);
    } catch {}
  }
}

function onSpawn(event) {
  system.run(() => {
    const p = event.player;
    if (!isOwner(p)) return;
    markOwner(p);
  });
}

function register() {
  if (registered) return;
  registered = true;

  if (world.beforeEvents?.playerBreakBlock) {
    world.beforeEvents.playerBreakBlock.subscribe(onBreakBefore);
  } else {
    world.afterEvents.playerBreakBlock.subscribe(onBreakAfter);
  }

  if (world.afterEvents.playerSpawn) {
    world.afterEvents.playerSpawn.subscribe(onSpawn);
  }

  system.runTimeout(() => {
    for (const p of world.getAllPlayers()) {
      if (isOwner(p)) markOwner(p);
    }
  }, 60);

  try {
    console.warn("[veinminer] v1.0.22 ores-only + destroy drops");
  } catch {}
}

register();
if (world.afterEvents.worldLoad) {
  world.afterEvents.worldLoad.subscribe(register);
}
