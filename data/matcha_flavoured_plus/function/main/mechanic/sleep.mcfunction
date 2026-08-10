# Reset first because scoreboard entries persist after a player leaves a bed.
# The per-player execution also avoids @p resolving to the wrong player in multiplayer.
execute as @a[gamemode=!spectator] run scoreboard players set @s sleepTimerScore 0
execute as @a[gamemode=!spectator] store result score @s sleepTimerScore run data get entity @s SleepTimer

# Advance the clock once only when every non-spectator player is asleep.
# Players in another dimension still count, so an awake player can never be skipped.
execute if entity @a[gamemode=!spectator] unless entity @a[gamemode=!spectator,scores={sleepTimerScore=..0}] unless entity @a[gamemode=!spectator,scores={sleepTimerScore=100..}] run time add 120
