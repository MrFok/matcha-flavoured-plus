execute unless score @s Hearts matches 20..60 run scoreboard players set @s Hearts 20
execute if score @s Hearts matches 60.. run advancement revoke @s only main:mechanics/heart_container_obtained
execute if score @s Hearts matches ..58 run function main:mechanic/clear_heart_container
