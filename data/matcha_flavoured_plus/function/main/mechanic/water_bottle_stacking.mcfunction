advancement revoke @s only matcha_flavoured_plus:main/mechanics/stack_water_bottles
execute store result score @s waterBottleCount run clear @s minecraft:potion[potion_contents={potion:"minecraft:water"},!max_stack_size=64]
execute if score @s waterBottleCount matches 1.. run execute store result storage matcha_flavoured_plus:main/water_bottle_stack count int 1 run scoreboard players get @s waterBottleCount
execute if score @s waterBottleCount matches 1.. run function matcha_flavoured_plus:main/mechanic/water_bottle_stacking/give with storage matcha_flavoured_plus:main/water_bottle_stack
scoreboard players reset @s waterBottleCount
