# Datapacks cannot register separate Creative-tab entries for component variants.
# Use /function main:divine/give_test_kit to test the Divine items directly.
give @s minecraft:feather[minecraft:custom_data={matcha:{divine_fragment:true}},minecraft:item_name={text:"Fragment of Tyrael's Wings",color:"aqua",italic:false},minecraft:item_model="minecraft:fragment_of_tyraels_wings",minecraft:rarity="epic",minecraft:max_stack_size=1,minecraft:lore=[{text:"A fragment of divine favour.",color:"gray",italic:true}]]
function main:divine/give_pickaxe_test_set
function main:divine/give_dolabra_test_set
tellraw @s {text:"Divine test kit granted: Pickaxe and Dolabra at Efficiency I-V.",color:"aqua"}
