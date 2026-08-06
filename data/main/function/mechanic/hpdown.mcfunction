execute as @a[scores={deaths=1..}] unless score @s Hearts matches 10..60 run scoreboard players set @s Hearts 20
execute as @a[scores={deaths=1..,Hearts=12..}] run scoreboard players remove @s Hearts 2
execute if entity @a[scores={deaths=1..}] run function main:mechanic/set_max_hp
execute as @a[scores={deaths=1..}] run scoreboard players set @s deaths 0
