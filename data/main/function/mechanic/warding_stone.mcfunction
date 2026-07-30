execute at @e[type=minecraft:armor_stand,tag=WardingStone] unless entity @e[distance=..16,type=#main:villager_friends,nbt={active_effects: [{id: "minecraft:regeneration"}]}] run effect give @e[type=#main:villager_friends,distance=..16] minecraft:regeneration 3 0 true
execute as @e[type=minecraft:armor_stand,tag=WardingStone,tag=!WardingStoneSetup] at @s run function main:mechanic/warding_stone_check_forbidden
function main:mechanic/warding_stone_effects
execute as @e[type=minecraft:armor_stand,tag=WardingStoneSetup] at @s unless block ~ ~ ~ minecraft:lodestone run function main:mechanic/warding_stone_killer
