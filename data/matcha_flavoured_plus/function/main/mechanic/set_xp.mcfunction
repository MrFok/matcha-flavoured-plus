tag @p add ExcludeFromXPRemoval
xp set @p 50 levels
scoreboard players set @p anvil_interaction 0
execute at @p run schedule function matcha_flavoured_plus:main/mechanic/clear_xp_tag 15s