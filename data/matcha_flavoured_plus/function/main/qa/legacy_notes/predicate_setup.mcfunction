kill @e[type=minecraft:armor_stand,tag=matcha_qa_predicate]
execute unless dimension minecraft:overworld run tellraw @s {"text":"FAIL: run this outdoors in the Overworld.","color":"red"}
execute if dimension minecraft:overworld at @s run summon minecraft:armor_stand ~ ~2 ~ {Tags:["matcha_qa_predicate"],NoGravity:1b,Invisible:1b,Invulnerable:1b}
execute as @e[type=minecraft:armor_stand,tag=matcha_qa_predicate,limit=1] at @s if predicate matcha_flavoured_plus:main/sky_spawn run say MATCHA_QA_PREDICATE_PASS
execute as @e[type=minecraft:armor_stand,tag=matcha_qa_predicate,limit=1] at @s unless predicate matcha_flavoured_plus:main/sky_spawn run say MATCHA_QA_PREDICATE_FAIL
kill @e[type=minecraft:armor_stand,tag=matcha_qa_predicate]
