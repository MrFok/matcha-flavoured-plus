# Matcha Flavoured Plus Lite

The vanilla, datapack-only edition of [Matcha Flavoured Plus](https://github.com/MrFok/matcha-flavoured-plus).
It targets Minecraft Java Edition 26.2 and requires no Fabric, Quilt, Forge,
NeoForge, or other mod loader.

Lite contains the Plus gameplay changes that can be implemented with a
datapack, plus a separate resource-pack archive for the custom visuals. It
does not contain Java entrypoints or loader-only behavior. See
[BRANCHES.md](BRANCHES.md) for the relationship with `upstream-fixes` and the
full Fabric edition on `main`.

## Install

Build the distribution:

```powershell
python tools/build_distribution.py
```

The build produces:

- `matcha_flavoured_plus-1.0.0-clean-tabs-datapack.zip`
- `matcha_flavoured_plus-1.0.0-dungeons-and-taverns-compatible-datapack.zip`
- `matcha_flavoured_plus-1.0.0-resource-pack.zip`

Install exactly one gameplay archive in the target world's `datapacks`
folder. Use the Dungeons & Taverns-compatible archive when that datapack is
installed; otherwise use `clean-tabs`. Do not unzip the archive.

Install the resource-pack archive in the client's `resourcepacks` folder and
enable it in Minecraft. Every multiplayer client should enable it to see the
custom names, models, textures, sounds, and UI assets.

For a dedicated server, place the gameplay archive in
`<server>/<world>/datapacks/`, then restart the server or run:

```mcfunction
/reload
/datapack list enabled
```

The datapack should appear in the enabled list. Lite is not installed in a
`mods` folder.

## Included behavior

- Managed extended-day sleep, including an all-players-in-bed multiplayer
  quorum.
- Instant Crystal Heart consumption and the permanent-heart death penalty.
- Reworked hunger, food, cooking, Estus, progression, alloys, equipment,
  repairs, trades, fishing, mobs, worldgen, and tutorials.
- Crafted/blessing-based custom enchantments rather than normal XP/table
  enchanting.
- An enchanting table recipe filter and 2–5 random enchanted books when a
  table is broken.
- The Tyrael's Wings survival recipe is intentionally removed and reserved
  for later design work.

## Known Lite boundaries

The vanilla enchanting-table screen still opens when the block is right-clicked;
cancelling that interaction requires the Fabric edition. Deterministic
percentage-based death loss through nested containers, spawner-origin loot
suppression, and client HUD rendering changes are also outside datapack-only
scope. Component-restricted Divine tool upgrades are reserved for the Fabric
edition because vanilla smithing recipes cannot inspect the required custom
item data. See [docs/capability-matrix.md](docs/capability-matrix.md).

## Verification

```powershell
python -m unittest discover -s tests -v
python tools/build_distribution.py
```

The automated tests validate JSON, archive boundaries, model references,
recipes, loot tables, smithing preservation, deterministic rebuilds, and other
static contracts. They complement—rather than replace—manual Minecraft
multiplayer testing.

## Upstream and license

The upstream project is [Matcha Flavoured](https://modrinth.com/datapack/matcha-flavoured)
by Klei Wright (`klei_wright`). See [CREDITS.txt](CREDITS.txt) for attribution.

This derivative is shared under
[CC-BY-NC-SA-4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
