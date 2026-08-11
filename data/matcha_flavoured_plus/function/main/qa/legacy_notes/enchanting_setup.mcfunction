give @s minecraft:enchanting_table 1
give @s minecraft:diamond_pickaxe 1
give @s minecraft:diamond_pickaxe[minecraft:enchantments={"minecraft:silk_touch":1}] 1
give @s minecraft:bookshelf 15
give @s minecraft:lapis_lazuli 64
give @s minecraft:diamond_sword 1
tellraw @s {"text":"Enchanting QA ready. Break an enchanting table with the plain diamond pickaxe: PASS = exactly 4 obsidian. Break one with the Silk Touch pickaxe: PASS = the enchanting table. The setup also contains the materials for a normal level-30 enchanting check.","color":"aqua"}
