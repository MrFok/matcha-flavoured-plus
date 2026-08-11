# Craft the supplied inputs at a smithing table, then run
# /function matcha_flavoured_plus:main/smithing_enchantments/test/check_regression
give @s minecraft:diamond_sword[minecraft:enchantments={"minecraft:sharpness":5,"minecraft:unbreaking":3}]
give @s minecraft:diamond
give @s minecraft:heart_of_the_sea
give @s minecraft:iron_chestplate[minecraft:enchantments={"minecraft:protection":4,"minecraft:mending":1}]
give @s minecraft:iron_ingot
give @s minecraft:resin_brick
tellraw @s {"text":"Smith the Sharpness V diamond sword into an Electrum Sword and the Protection IV iron chestplate into Steel, then run the smithing regression check.","color":"yellow"}
