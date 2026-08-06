# Branch responsibilities

## `upstream-fixes`

This branch starts from the imported Matcha Flavoured 1.03 release and contains
only compatibility work and fixes for issues documented by the original creator.

| Change | Included | Notes |
| --- | --- | --- |
| Minecraft 26.2 data/resource compatibility | Yes | Repairs current resource paths and schemas. |
| Sleep initialization without relog or `/reload` | Yes | Creates the objective before assigning constants. |
| Multiplayer Heart Container isolation | Yes | Preserves upstream automatic acquisition while targeting the correct player. |
| Sweet-berry effect for plain/fox-held berries | Yes | Keys behavior to `minecraft:sweet_berries`. |
| Smithing enchantment preservation | Yes | Preserves base enchantments and adds material minimums. |
| Feather Falling protection from ender-pearl damage | Yes | Uses an ender-pearl-specific damage-type tag. |
| Spawner-origin loot suppression | No | Still unresolved. |
| Automatic vanilla Modrinth world installation | No | Vanilla datapacks still require a target world's `datapacks` directory. |
| Matcha Flavoured Plus custom content | No | Intentionally excluded. |

The branch builds one loader-free combined ZIP for manual installation as both a
world datapack and client resource pack.

## `main`

This is the Matcha Flavoured Plus branch. It includes the upstream fixes plus the
project's intentional packaging, balance, compatibility, and quality-of-life
changes.

| Change | Included | Notes |
| --- | --- | --- |
| Creator-reported fixes from `upstream-fixes` | Yes | Adapted where Plus intentionally changes behavior. |
| Vanilla datapack/resource-pack artifacts | Yes | Separate manual-install archives. |
| Self-contained Modrinth mod JARs | Yes | Fabric is verified; other declared loaders remain experimental. |
| Dungeons & Taverns advancement-tab variant | Yes | Separate compatible build. |
| Divine Adamant axe, dolabra, and pickaxe upgrades | Yes | Plus-only progression and visual content. |
| Deliberate Heart Container consumption | Yes | Plus behavior differs from upstream automatic acquisition. |
| Structure-only enchanting tables | Yes | Plus-specific balance change. |
| Warding Stone, water-bottle, asset, and HUD corrections | Yes | Plus maintenance fixes. |
| Divine Elytra | No | Removed; it is not part of either branch. |
