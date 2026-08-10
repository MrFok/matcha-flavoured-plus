scoreboard players set @s Hearts 20
function matcha_flavoured_plus:main/mechanic/set_max_hp
tellraw @s {"text":"Death QA ready. Run /attribute @s minecraft:max_health get, then /kill @s. After respawning, run /scoreboard players get @s Hearts and /attribute @s minecraft:max_health get. PASS only if both are 18.","color":"aqua"}
