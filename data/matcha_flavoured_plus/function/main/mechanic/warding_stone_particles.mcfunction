playsound minecraft:entity.wither.spawn block @a ~ ~ ~ .25
execute unless block ~ ~ ~ minecraft:lodestone run setblock ~ ~ ~ minecraft:lodestone
particle minecraft:sculk_soul ~ ~.5 ~ .25 .1 .25 .05 10
particle minecraft:soul_fire_flame ~ ~.5 ~ .5 .1 .5 .1 10
tag @s add WardingStoneSetup
