execute if items entity @s container.* *[minecraft:item_model="minecraft:heart_container"] run scoreboard players add @s Hearts 2
execute if items entity @s container.* *[minecraft:item_model="minecraft:heart_container"] run tag @s add AddingHearts
execute if items entity @s container.* *[minecraft:item_model="minecraft:heart_container"] run effect give @s regeneration 3 10 true
execute if items entity @s container.* *[minecraft:item_model="minecraft:heart_container"] run clear @s *[minecraft:item_model="minecraft:heart_container"] 1
playsound minecraft:item.totem.use player @s[tag=AddingHearts] ~ ~ ~ .5 0 0
advancement revoke @s[tag=AddingHearts] only main:mechanics/heart_container_obtained
function main:mechanic/set_max_hp
execute if items entity @s container.* *[minecraft:item_model="minecraft:heart_container"] run function main:mechanic/process_heart_container
