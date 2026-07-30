# Matcha Flavoured Plus — Feature Matrix

This matrix describes the features implemented in the local Minecraft 26.2 data/resource pack (version 1.03). Counts refer to raw definitions, not necessarily distinct player-facing outputs.

| System | Implemented features | Local scope |
|---|---|---|
| Pack architecture | Combined data/resource pack. Gameplay is driven by load/tick functions, JSON recipes, loot tables, trades, advancements, worldgen, models, textures, sounds, and language overrides. | 94 functions, 222 advancements, 282 loot tables, 235 trades, 75 worldgen files. |
| Global rules | Disables natural health regeneration; enables keep inventory; removes phantoms; reduces explosion-drop loss; preserves ender pearls on death; controls time progression. | `data/main/function/setup/gamerules.mcfunction` |
| Extended days / sleep | Slows the normal day cycle and replaces normal sleeping with a managed sleep/time-advance system. | `data/main/function/environmental`, `data/main/function/mechanic/sleep*` |
| Hunger redesign | Hunger is no longer a normal survival limiter; high hunger triggers a hunger effect and low hunger gets saturation support. Food is intended as healing and buff delivery. | `data/main/function/mechanic/manage_hunger.mcfunction` |
| Food intrinsics | Food ingredients carry gameplay effects; cooking, preservation, and meals form progression chains rather than simple saturation upgrades. | 122 recipe definitions in `data/food/recipe` |
| Food content | Preserves, jams, breads, doughs, flours, pickles, hot foods, basic meals, golden-food variants, pumpkin dishes, curry dishes, ramen, paneer makhani, and secret meals. | Food, campfire, smoking, blasting, and crafting recipe namespaces. |
| Cooking stations | Campfire, mud kiln, kiln, oven, bowl/ceramic progression, plus early-game grass/dry-grass fuel workflow. | Tutorial advancements and food/crafting recipes. |
| Death model | Keep inventory; deaths deduct one permanent heart rather than deleting carried items. | `data/main/function/mechanic/hpdown.mcfunction` |
| Crystal Hearts | Permanent maximum-health upgrades, capped at 30 hearts. | `data/main/function/mechanic/process_heart_container.mcfunction` |
| Early progression | Custom tutorial path centered on wood → copper → iron, explicitly replacing vanilla stone-tool progression. | Recipe/advancement suppression plus tutorial advancements. |
| Early utility | Early craftable shulkers, bundles, basic ceramics, campfire/kiln infrastructure, and reduced inventory friction. | Crafting and tutorial definitions. |
| Hybrid tools | Dolabras combine pickaxe and axe functions; Mattocks combine shovel and hoe functions. | Smithing/crafting recipes and tool models. |
| Metal/alloy paths | Bronze, Steel, Electrum, Shakudo/Palatinate, and Adamant gear paths; alloy-specific tools, armour, and progression gates. | 70 smithing recipes in `data/smithing_table/recipe` |
| Steel progression | Carbon-Rich Iron intermediary, then Steel Alloy via blasting; steel emphasizes durability and defensive properties. | `data/crafting/recipe/carbon_rich_iron.json`, `data/blasting/recipe/steel_alloy.json` |
| Electrum progression | Late-game alloy path tied to Divine Fragments; equipment supports anti-undead gameplay and high Fortune/Looting themes. | Smithing recipes and custom enchantments. |
| Shakudo / Palatinate | Silk Touch and cleansing-oriented equipment identity. | Smithing recipes, item definitions, and custom enchantment effects. |
| Adamant | Divine/endgame alloy with special repair requirements and late-progression positioning. | Smithing recipes, advancements, and repair functions. |
| Equipment overhaul | Custom knives, cleavers, silver sword, warding sword, warding shield, jewellery, Nazar, gilded boots, metal armour/tool variants, and renamed vanilla materials. | Models, language entries, smithing/crafting recipes. |
| Endless repairs | Tools are intended to remain repairable indefinitely with appropriate base materials; XP is controlled to prevent vanilla-style progression from dominating. | `data/endless_repairs` and anvil/XP functions. |
| XP redesign | Continuously removes normal XP while temporarily granting controlled XP for repair-related flows. | `data/main/function/mechanic/remove_xp.mcfunction`, `set_xp.mcfunction` |
| Crafted enchanting | Enchantments are acquired through recipes/blessings rather than enchantment-table randomness and XP grinding. | 23 blessing recipes in `data/blessings/recipe` |
| Custom enchantments | Anemos, Bloodrage, four Cleanses, Conduit Power, Divinity, Fire Proof, Frost Protection, Haste, Reach, Regeneration, Riposte, Sanguine, Slaughter, Traversal, Warding Armour, four Warding tiers, and Zephyr. | 23 definitions in `data/main/enchantment` |
| Estus system | Raw Estus is processed into a healing/resistance effect and Estus Ash; Stabilised Estus participates in higher progression. | `data/main/function/mechanic/check_if_estus_should_be_processed.mcfunction` |
| Divine economy | Divine Fragments and Divine Favours gate Crystal Hearts, Adamant, Electrum, End-related progression, enchantments, and special tools. | Loot tables, advancements, blessings, and recipes. |
| Warding Stones | Placeable base-defense system: wards nearby undead, harms them, produces effects, and regenerates allied villagers/friends. | `data/main/function/mechanic/warding_stone*.mcfunction` |
| Trial Chamber constraint | Warding Stones are forcibly removed and trigger an explosion/effects in Trial Chambers. | `data/main/advancement/mechanics/enter_trial_chamber.json` |
| Undead surface | Overworld surface prioritizes undead; non-undead mundane hostiles are suppressed when outdoors. | Spawn-management functions. |
| Mob balance | Fast zombies, modified husks, half-health skeletons, weaker creepers, fast low-health cave spiders, zero equipment-drop chance, and altered undead drops. | `data/main/function/spawn_mechanic`, entity loot tables. |
| Dragon aftermath | Killing the first Dragon activates a safer surface state: many hostile surface spawns are removed while underground danger remains. | `data/main/function/first_dragon_killed_reward.mcfunction`, `safe_surface.mcfunction` |
| Creature drops | Rotten-flesh replacement/alteration, tattered leather, Estus-related drops, modified structure/entity/block loot, and custom treasure pools. | 282 tables in `data/minecraft/loot_table` |
| Fishing overhaul | 50 named fish, biome-specific fishing pools, freshwater/saltwater/deep-dark/pale-garden/swamp/sulfur-cave variants, treasure, and fishing trade economy. | `data/minecraft/loot_table/gameplay/fishing` |
| Villager economy | 235 custom trade definitions across villagers and wandering traders; trades are broadly high-use and replace vanilla sell-everything loops. | `data/minecraft/villager_trade` |
| Fisherman role | Fishermen buy caught fish and form the primary player-to-villager sales loop. | 48 fisherman trade definitions. |
| Wandering trader | Sells maps, music discs, asylum-seeker applications, special items, and exploration-facing goods. | 33 wandering-trader definitions. |
| Refugee villagers | Asylum-seeker/application trade system that spawns culturally distinct villagers. | Wandering-trader trade definitions and tutorial/advancement hooks. |
| Other professions | Reworked Armorer, Cartographer, Cleric, Farmer, Leatherworker, Librarian, Mason, Shepherd, Toolsmith, Butcher, and others; bulk-building materials and specialist resources are tradeable. | Trade folders by profession. |
| Currency | Renames emeralds to Obols and restructures their economic role. | Resource-pack language and trade data. |
| Exploration maps | Cartographers sell maps for mineshafts, witch huts, temples, jungle ruins, trail ruins, monuments, Trial Chambers, warm ruins, Ancient Cities, and mansions. | Cartographer trade definitions. |
| Resource conversion | Large-scale recipes for material conversion, including copper-to-prismarine and broad block transformation paths. | 459 crafting and 327 stonecutting recipes. |
| Stonecutting overhaul | Extensive stonecutter catalog, including generous conversions and building-material access. | `data/stonecutting/recipe` |
| Block/structure loot | Overrides major chest, archaeology, block, entity, shearing, harvesting, and gameplay loot tables. | 282 custom/overridden loot tables. |
| Villages | Replaces/extends village generation with beta-style village structures and pools. | 16 NBT village structures plus worldgen structure/template-pool files. |
| Biome/world visuals | 65 overridden biome files, modified ecology/spawn presentation, and broad world aesthetic changes. | `data/minecraft/worldgen` |
| Weather statues | Craftable statue system for changing weather. | Mechanical functions and crafting recipes. |
| Freezing water | Water/freezing environmental hazard with Slowness, Darkness, and freeze damage. | `data/main/function/environmental/freezing_water.mcfunction` |
| Music | Custom music-disc content, jukebox-song definitions, and wandering-trader music access. | `data/custom_music`, `data/main/jukebox_song`, trade data. |
| UI/art overhaul | Custom item/block/entity/GUI textures, models, block states, armour equipment, sounds, and four English language variants. | 1,641 textures and 699 models in `assets`. |
| Vanilla renaming | Many vanilla items are recontextualized: emerald → Obol, blaze powder → Raw Estus, glowstone dust → Estus Ash, nether star → Divine Favour, turtle scute → Divine Fragment, etc. | `assets/minecraft/lang/en_us.json` |
| Custom visual content | Custom foods, metals, jewellery, books, fish, warding objects, tools, armour, utility objects, pride banners, and musical assets. | Item models/textures and language definitions. |
| Secrets and discovery | Secret ingredients, secret foods/meals, hidden enchantments, special books, special treasures, and advancement-led discovery. | Recipe, advancement, enchantment, loot, and language data. |
| Tutorials | Guided advancement sequence for harvesting, campfires, kilns, metals, food preservation, trades, equipment, Nether/End progression, Divine Fragments, and secrets. | 57 tutorial advancements. |
| Accessibility / QoL | No hunger-management treadmill, recoverable death loop, persistent repairs, early storage, reduced hotbar clutter, broad material conversion, and in-pack tutorials. | Cross-cutting implementation. |

## Change boundaries

| Area | Primary implementation locations |
|---|---|
| Food, healing, hunger | `data/main/function/mechanic`, `data/food/recipe`, food loot tables |
| Death and maximum health | `hpdown.mcfunction`, `process_heart_container.mcfunction`, Crystal Heart recipes/loot |
| Mob ecology / Dragon world-state | `data/main/function/spawn_mechanic`, `first_dragon_killed_reward.mcfunction`, entity loot |
| Warding | `warding_stone*.mcfunction`, Trial Chamber advancement |
| Gear and alloys | `data/smithing_table/recipe`, `data/crafting/recipe`, `data/blasting/recipe` |
| Enchanting / Divine gating | `data/blessings/recipe`, `data/main/enchantment`, loot tables |
| Economy and maps | `data/minecraft/villager_trade` |
| Exploration, fishing, structures | `data/minecraft/loot_table`, `data/minecraft/worldgen` |
| Visual identity | `assets/minecraft/models`, `textures`, `lang`, `sounds` |

## Core gameplay loop

Explore, fish, and fight to acquire unusual materials and Divine resources; cook or craft specialized effects and gear; trade for location and infrastructure access; progress without AFK farms or random enchanting.

## Detailed additions by content family

### Food recipes added

The food namespace contains these named food/product families. Most have a normal recipe plus a campfire, preservation, or intermediate variant where applicable:

- Apple Empanada; Baked Apple; Baked Golden Apple; Baked Potato; Baked Pumpkin.
- Bokguk; Braised Brown Mushroom; Braised Crimson Fungus; Braised Red Mushroom; Braised Warped Fungus.
- Bread; Brownie; Bruschetta; Cake; Carrot Cupcake; Golden Carrot Cupcake.
- Canned Apple; Canned Golden Apple; Cheese; Chocolate; Chocolate Chip Cookie; Chocolate Campfire.
- Charred Fish; Charred Meat; Charred Potato; Cooked Beef; Cooked Chicken; Cooked Cod; Cooked Mutton; Cooked Pork; Cooked Pufferfish; Cooked Rabbit; Cooked Salmon; Cooked Tropical Fish.
- Crimson Stroganoff; Red Mushroom Stroganoff; Warped Stroganoff.
- Dough; Dough from Water; Flour; Flour Bag; Flour from Flour Bag.
- French Toast; Honied French Toast; Fried Egg; Gimmari; Glow Berry Crumble; Glow Jam; Glow Mash.
- Gnocchi; Golden Apple; Golden Apple Empanada; Golden Carrot; Golden Pickled Carrots; Golden Steamed Carrots.
- Green Curry; Japanese Curry; Paneer Makhani; Ramen, including uncooked variants.
- Grilled Melon; Grilled Tomatoes; Honey Ginger Tea; Latke; Mead; Melon Sorbet; Milk Bottle.
- Naan; Pickled Carrots; Pickled Crimson Fungus; Pickled Mushrooms; Pickled Potatoes; Pickled Red Mushrooms; Pickled Tomatoes; Pickled Warped Fungus.
- Popped Chorus Fruit; Pumpkin Empanada; Pumpkin Jam; Pupusa.
- Steamed Carrots; Stroganoff; Sugar from Honey Bottle; Sweet Berry Danish; Sweet Berry Jam; Sweet Berry Mash; Sweet Berry Toast.
- Uncooked Curry; Uncooked Green Curry; Uncooked Paneer Makhani; Warped Stroganoff.

### Equipment and alloy additions

The smithing namespace adds the following concrete equipment families:

- Adamant: axe, boots, chestplate, claymore, Dolabra, helmet, hoe, leggings, Mattock, pickaxe, shovel, spear, sword.
- Bronze: axe, boots, chestplate, Dolabra, Elytra, helmet, hoe, leggings, Mattock, pickaxe, shovel, spear, sword.
- Electrum: axe, boots, chestplate, Dolabra, helmet, hoe, leggings, Mattock, pickaxe, shovel, spear, sword.
- Shakudo: axe, boots, chestplate, Dolabra, helmet, hoe, leggings, Mattock, pickaxe, shovel, spear, sword.
- Steel: axe, boots, chestplate, Dolabra, helmet, hoe, leggings, Mattock, pickaxe, shears, shovel, spear, sword.
- Supporting equipment: Silver Sword, Warding Sword, Warding Shield, Lesser Warding Shield, Butcher Knife, Gilded Leather Boots.
- Jewellery smithing: Amber Earrings, Opal Earrings, Topaz Earrings, Ruby Circlet, Bronze Laurel.
- Base-metal progression: Copper, Iron, Diamond, alloy, and Adamant tool/armour variants, including spears and hybrid tools.

### Exact custom enchantment identifiers

`anemos`, `bloodrage`, `cleanse_armor_chest`, `cleanse_armor_feet`, `cleanse_armor_head`, `cleanse_armor_legs`, `conduit_power`, `divinity`, `fire_proof`, `freezing_protection`, `haste`, `reach`, `regeneration`, `riposte`, `sanguine`, `slaughter`, `traversal`, `warding_armour`, `warding0`, `warding1`, `warding2`, `warding3`, and `zephyr`.

Their player-facing names include Anemos, Bloodrage, Cleanses, Conduit Power, Divinity, Fire Proof, Frost Protection, Haste, Reach, Regeneration, Riposte, Sanguine, Slaughter, Traversal, Apotropaic/Warding Armour, Faint Warding, Lesser Warding, Warding, Greater Warding, and Zephyr.

### Exact runtime systems

The 94 functions are organized into these implemented systems:

- Setup: load, scoreboard creation, gamerules, tick registration, and the central ticking-function dispatcher.
- Hunger and survival: hunger management, sleeping, Crystal Heart state, maximum-health updates, death penalty, XP removal/set/reset, water-bottle stacking, and Estus processing.
- Warding: placement, particles, sound, undead damage/slowness, allied regeneration, Trial Chamber removal, and warding-stone kill behavior.
- Mob ecology: spawn filtering, mob-stat modification, tick processing, safe-surface activation after the Dragon, and undead surface management.
- Enchantment effects: Anemos, Bloodrage, four armour cleanses, Conduit Power, Divinity, Fire Proof, Haste, Regeneration, Slaughter, Warding Armour, four Warding levels, and Zephyr execution/failure handling.
- Environmental systems: extended day cycle, freezing water, stalking behavior, player stepping sounds, eerie village ambience, weather changes, and clay-statue weather effects.
- Utility items: Bedrock Buster, Happy Ghast Horn, invisible item frames, soul-sight glow effects, boat boarding/riding particles, Divine Favour particles, and sulfurous-hellstone particles.

### Exact villager and trader additions

- Armorer: redstone/technical components, comparator, composter, note block, redstone block, repeater, redstone lamp, target, waxed copper bulb, dispenser, dropper, hopper, observer, crafter, pistons, sticky pistons, lava kit.
- Butcher: Sweet Berry Toast, Warped Stroganoff, Chorus Mochi, Butcher Knife, and filler trades.
- Cartographer: maps to Mineshaft, Witch Hut, Desert Temple, Jungle Ruin, Trail Ruin, Ocean Monument, Trial Chamber, Warm Ocean Ruin, Ancient City, and Woodland Mansion, plus pottery sherds and brushes.
- Cleric: splash potions including Infested, Invisibility, Oozing, Pitch, Poison, Slowness, Weakness, Weaving, Wind Charged, and Wither.
- Farmer: bone meal, seed bundles, floral/mushy/exotic bundles, colored eggs, and baby cold/temperate/warm cow and pig eggs.
- Fisherman: named fish purchasing trades for common, freshwater, saltwater, deep-water, and rare fish.
- Fletcher: ordinary, spectral, compound, Apotropaic, and Nightshade arrows.
- Leatherworker: every major wood/log type, mushroom stem, Pale Oak, and hatchet.
- Librarian: Divine Comedy, Paradise Lost, The Avesta, Book of Enoch, Solomon-related books, Ender Pearls, and special treasures such as Crystal Hearts.
- Mason: bulk Andesite, Diorite, Granite, Stone, Deepslate, Glass, Smooth Sandstone, Smooth Red Sandstone, Terracotta, Tuff, Calcite, Flowstone, Malachite, Blackstone, Quartz, Smooth Basalt, and Smooth Quartz.
- Shepherd: all wool colors, baby sheep eggs, Shepherd's Shears, and Crook.
- Toolsmith: Opal Earrings, Ruby Circlet, Amber Earrings, Bronze Laurel, Topaz Earrings, and gemstone selling trades.
- Wandering Trader: adult/child Asylum Seeker applications, village maps, Witch Hut map, music discs, and exploration goods.
- Weaponsmith: IOU and filler progression.

### Exact fishing additions

Fishing loot contains 50 named fish, including Alaska Blackfish, Anchovy, Bluegill, Bujurqui, Cod, Crappie, Freshwater Pufferfish, Guppy, Humpback Whitefish, Mediterranean Killifish, Pufferfish, Rainbow Wrasse, Salmon, Shad, Striped Perch, Black Seabass, Carp, Flying Fish, Gurnard, Herring, Lamprey, Mahi Mahi, Piranha, Spoonhead Sculpin, Walleye, Armoured Catfish, Catfish, Flounder, Gar, Monkfish, Northern Pike, Painted Moray, Sturgeon, Tunisian Barb, Wolffish, Arapaima, Bass, Echo Fish, European Eel, Muskellunge, Oarfish, Opah, Pale Fish, Siberian Sturgeon, Skate, and Swordfish, with biome/depth-specific pools and treasure tables.

### Exact custom item/name additions

The resource pack recontextualizes vanilla materials and adds named gameplay items including Crystal Heart, Bedrock Buster, Warding Stone, Nazar, Obol, Raw Estus, Estus Ash, Stabilised Estus, Divine Favour, Divine Fragment, Electrum Alloy, Hepatizon Alloy, Shakudo Alloy, Steel Alloy, Carbon-Rich Iron, Bronze Alloy, Amber, Opal, Ruby, Topaz, jewellery, weather statues, invisible item frames, special books, custom fish, food products, alloy equipment, custom arrows, music discs, and utility items.

Important vanilla name changes include emerald → Obol, netherite → Adamant, redstone → Electric Wire, gunpowder → Sulfur Chunk, blaze powder → Raw Estus, glowstone dust → Estus Ash, blaze rod → Stabilised Estus, nether star → Divine Favour, turtle scute → Divine Fragment, heart of the sea → Electrum Alloy, phantom membrane → Hepatizon Alloy, shulker shell → Shakudo Alloy, and resin brick → Steel Alloy.

### Exact world/resource additions

- 65 biome overrides for visual, ecology, and spawn behavior.
- Beta-style village structures, template pools, and structure sets.
- 282 loot-table overrides covering blocks, entities, chests, archaeology, fishing, shearing, harvesting, food, spawners, Trial Chambers, and custom items.
- 10 pride banner patterns.
- Jukebox-song and custom music definitions, including a Golden music disc.
- 1,641 textures: 659 item, 491 block, 244 GUI, 183 entity, and other supporting textures.
- 699 models: 477 item models and 222 block models, plus equipment, blockstate, sound, and language assets.
- Tutorial and discovery advancements for campfires, kilns, metals, alloy gear, food, fishing, trades, Nether/End progression, secrets, Crystal Hearts, Divine resources, and special meals.
