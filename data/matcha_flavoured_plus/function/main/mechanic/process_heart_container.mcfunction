execute unless score @s Hearts matches 10..60 run scoreboard players set @s Hearts 20
execute if score @s Hearts matches 60.. run loot give @s loot minecraft:kleis_items/crystal_heart
execute if score @s Hearts matches 60.. run tellraw @s {"text":"Your heart capacity is already full.","color":"red"}
execute if score @s Hearts matches ..58 run scoreboard players add @s Hearts 2
execute if score @s Hearts matches ..58 run effect give @s regeneration 3 10 true
execute if score @s Hearts matches ..58 run playsound minecraft:item.totem.use player @s ~ ~ ~ 0.5 0
execute if score @s Hearts matches ..58 run function matcha_flavoured_plus:main/mechanic/set_max_hp
advancement revoke @s only matcha_flavoured_plus:main/mechanics/heart_container_obtained
