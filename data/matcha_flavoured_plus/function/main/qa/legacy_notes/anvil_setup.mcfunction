give @s minecraft:anvil 1
give @s minecraft:iron_sword[minecraft:damage=200] 1
give @s minecraft:iron_ingot 3
tellraw @s {"text":"Anvil QA ready. Place and use the anvil to repair or rename the sword, then take the output. PASS A: your XP becomes 50. Close the anvil and wait 16 seconds. PASS B: the XP is cleared.","color":"aqua"}
