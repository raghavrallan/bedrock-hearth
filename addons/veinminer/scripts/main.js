import { world, system, Player } from "@minecraft/server";

const OWNER_TAG = "friends_owner";
const OWNER_NAMES = new Set(["busyybeeee"]);

const VEIN_BLOCKS = new Set([
  // Overworld ores
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
  // Nether rare only (no netherrack / basalt / soul sand etc.)
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

const MAX_VEIN = 64;
const DIRS = [
  [1, 0, 0],
  [-1, 0, 0],
  [0, 1, 0],
  [0, -1, 0],
  [0, 0, 1],
  [0, 0, -1],
];

function isOwnerPlayer(entity) {
  if (!(entity instanceof Player)) return false;
  try {
    if (entity.hasTag(OWNER_TAG)) return true;
  } catch {
    // tag API unavailable
  }
  const name = (entity.name || "").trim().toLowerCase();
  return OWNER_NAMES.has(name);
}

function enableCoordinatesForAll() {
  for (const id of ["overworld", "nether", "the_end"]) {
    try {
      world.getDimension(id).runCommand("gamerule showcoordinates true");
    } catch {
      // dimension may be unavailable
    }
  }
}

function sameVeinBlock(block, typeId) {
  if (!block) return false;
  const id = block.typeId;
  if (id === typeId) return true;
  if (QUARTZ_ORES.has(id) && QUARTZ_ORES.has(typeId)) return true;
  return false;
}

function posKey(x, y, z) {
  return `${x},${y},${z}`;
}

function veinMine(dimension, start, typeId) {
  const queue = [{ x: start.x, y: start.y, z: start.z }];
  const seen = new Set([posKey(start.x, start.y, start.z)]);
  const extra = [];

  while (queue.length > 0 && extra.length < MAX_VEIN) {
    const cur = queue.shift();
    for (const [dx, dy, dz] of DIRS) {
      const nx = cur.x + dx;
      const ny = cur.y + dy;
      const nz = cur.z + dz;
      const k = posKey(nx, ny, nz);
      if (seen.has(k)) continue;
      seen.add(k);
      let block;
      try {
        block = dimension.getBlock({ x: nx, y: ny, z: nz });
      } catch {
        continue;
      }
      if (!sameVeinBlock(block, typeId)) continue;
      extra.push({ x: nx, y: ny, z: nz });
      queue.push({ x: nx, y: ny, z: nz });
    }
  }

  for (const loc of extra) {
    try {
      dimension.runCommand(`setblock ${loc.x} ${loc.y} ${loc.z} air destroy`);
    } catch {
      // skip unloaded chunks
    }
  }
}

function onBreak(event) {
  if (!isOwnerPlayer(event.player)) return;
  let typeId = event.brokenBlockPermutation.type.id;
  if (QUARTZ_ORES.has(typeId)) typeId = "minecraft:quartz_ore";
  if (!VEIN_BLOCKS.has(typeId)) return;
  try {
    if (event.player.isSneaking) return;
  } catch {
    // older API without isSneaking
  }
  const loc = event.block.location;
  const start = { x: Math.floor(loc.x), y: Math.floor(loc.y), z: Math.floor(loc.z) };
  const dimension = event.dimension;
  system.run(() => veinMine(dimension, start, typeId));
}

function clearLegacyGodEffects(player) {
  if (!(player instanceof Player)) return;
  const name = (player.name || "").trim().toLowerCase();
  if (name !== "busyybeeee") return;
  try {
    player.removeTag("friends_god");
  } catch {
    // ignore
  }
  try {
    const dim = player.dimension;
    const n = player.name;
    dim.runCommand(`effect "${n}" clear`);
    for (const fx of ["resistance", "regeneration", "fire_resistance", "saturation", "absorption", "health_boost"]) {
      dim.runCommand(`effect "${n}" ${fx} 0`);
    }
  } catch {
    // ignore
  }
}

function registerVeinMiner() {
  enableCoordinatesForAll();
  world.afterEvents.playerBreakBlock.subscribe(onBreak);
  system.runInterval(enableCoordinatesForAll, 60);
  if (world.afterEvents.playerSpawn) {
    world.afterEvents.playerSpawn.subscribe((event) => {
      system.run(() => clearLegacyGodEffects(event.player));
    });
  }
}

if (world.afterEvents.worldLoad) {
  world.afterEvents.worldLoad.subscribe(registerVeinMiner);
} else {
  registerVeinMiner();
}
