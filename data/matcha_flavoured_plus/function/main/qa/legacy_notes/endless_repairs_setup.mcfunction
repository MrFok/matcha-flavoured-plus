give @s minecraft:diamond_sword[minecraft:damage=1000,minecraft:repair_cost=20] 1
tellraw @s {"text":"Endless-repairs QA ready. Wait one second, then run /data get entity @s Inventory. PASS if the supplied diamond sword has no repair_cost component: Minecraft omits the default value of 0.","color":"aqua"}
