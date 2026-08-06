# Matcha Flavoured — Upstream Fixes

This branch preserves the gameplay and visual design of
[Matcha Flavoured 1.03](https://modrinth.com/datapack/matcha-flavoured) while
isolating correctness fixes for problems documented by its creator. It does not
contain Matcha Flavoured Plus features, Divine tool upgrades, Divine Elytra, or
loader metadata.

## Included fixes

| Creator-reported problem | Resolution |
| --- | --- |
| Sleeping requires a relog or `/reload` | Create `sleepTimerScore` before assigning its constants. |
| Heart Containers fail in multiplayer | Keep automatic acquisition behavior while targeting the triggering player instead of the nearest player. |
| Fox-held/plain sweet berries lack the intended effect | Apply berry behavior by the `minecraft:sweet_berries` item ID. |
| Material smithing replaces existing enchantments | Preserve the base enchantments and add only the material minimums after crafting. |
| Feather Falling does not affect ender-pearl damage | Add an ender-pearl-specific Feather Falling immunity effect. |

The requested spawner-origin loot suppression and a fully automatic vanilla
Modrinth installation are not implemented. Vanilla datapacks remain
world-specific, so the Modrinth App cannot choose a target world's `datapacks`
directory automatically.

## Installation

Run `python tools/build_distribution.py`, then place the generated combined ZIP
in both locations:

1. The target world's `datapacks` directory.
2. The client's `resourcepacks` directory.

No Fabric, Quilt, Forge, NeoForge, or other mod loader is required.

## Verification

```powershell
python tools/generate_smithing_enchantment_preservation.py --check
python -m unittest discover -s tests -v
python tools/build_distribution.py
```

The automated checks validate source JSON, player scoping, generated smithing
handlers, archive contents, and deterministic builds. Player-dependent behavior
should still be exercised with the supplied smithing regression kit and a
multiplayer Minecraft test before release.

## Attribution and license

The original project was created by Klei Wright (`klei_wright`). See
[CREDITS.txt](CREDITS.txt) for upstream attribution. This derivative remains
under CC-BY-NC-SA-4.0.
