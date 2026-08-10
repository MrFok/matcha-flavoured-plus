execute at @a run advancement revoke @p only matcha_flavoured_plus:main/mechanics/estus_obtained
execute if entity @p[gamemode=!creative] run function matcha_flavoured_plus:main/mechanic/process_estus

# In creative, items are refilled by the game. This means estus can never be cleared, and can cause serious issues, corrupting worlds.
# This is a band-aid fix for that issue. If you have a better idea, lmk