# Run /function main:divine/place_mining_test_wall in a clear test area.
# Creates five six-by-six walls, six blocks south (+Z) of the executor.

# Core mining-speed materials.
execute at @s run fill ~-11 ~1 ~6 ~-6 ~6 ~6 minecraft:stone
execute at @s run fill ~-4 ~1 ~6 ~1 ~6 ~6 minecraft:deepslate
execute at @s run fill ~3 ~1 ~6 ~8 ~6 ~6 minecraft:cobbled_deepslate

# Deepslate ore wall one.
execute at @s run fill ~10 ~1 ~6 ~15 ~1 ~6 minecraft:deepslate_coal_ore
execute at @s run fill ~10 ~2 ~6 ~15 ~2 ~6 minecraft:deepslate_copper_ore
execute at @s run fill ~10 ~3 ~6 ~15 ~3 ~6 minecraft:deepslate_iron_ore
execute at @s run fill ~10 ~4 ~6 ~15 ~4 ~6 minecraft:deepslate_gold_ore
execute at @s run fill ~10 ~5 ~6 ~15 ~5 ~6 minecraft:deepslate_redstone_ore
execute at @s run fill ~10 ~6 ~6 ~15 ~6 ~6 minecraft:deepslate_lapis_ore

# Deepslate ore wall two, with repeated high-value ores for mining-speed testing.
execute at @s run fill ~17 ~1 ~6 ~22 ~2 ~6 minecraft:deepslate_diamond_ore
execute at @s run fill ~17 ~3 ~6 ~22 ~4 ~6 minecraft:deepslate_emerald_ore
execute at @s run fill ~17 ~5 ~6 ~22 ~6 ~6 minecraft:deepslate_redstone_ore

tellraw @s {text:"Divine mining test wall placed six blocks south: stone, deepslate, cobbled deepslate, and deepslate ores.",color:"aqua"}
