#If the ender dragon is killed, we run to check the spawn with the safe surface predicate
execute if score gamerule gamerule_safe_surface matches 1 run execute as @e[type=#matcha_flavoured_plus:main/mundane_hostiles,tag=!SpawnChecked] run function matcha_flavoured_plus:main/mechanic/spawn_mechanic/safe_surface
#Otherwise, we just check to see if it is a sky spawn.
execute as @e[type=#matcha_flavoured_plus:main/mundane_hostiles,tag=!SpawnChecked] run function matcha_flavoured_plus:main/mechanic/spawn_mechanic/check_mob_spawn
