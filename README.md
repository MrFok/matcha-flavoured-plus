# Matcha Flavoured Plus - Fabric Edition

This is the full mod-oriented edition of [Matcha Flavoured Plus](https://github.com/MrFok/matcha-flavoured-plus), intended for Fabric servers and the clients that join them.

The `main` branch consumes the datapack-safe work from `lite` and is the home
for features that need Java, Fabric events, or client/server hooks. The current
distribution JAR packages the shared Matcha gameplay data and resource assets
into a loader-installable artifact. See [BRANCHES.md](BRANCHES.md) for the
three-branch flow.

## Requirements

- Minecraft Java Edition 26.2.
- Fabric Loader.
- Fabric API, including the Fabric resource loader.
- The same Matcha Flavoured Plus mod JAR on the dedicated server and every
  client that joins it.

Quilt, Forge, and NeoForge metadata is included for future compatibility, but
those loaders are not currently runtime-supported.

## Build

```powershell
python tools/build_distribution.py --include-mod
```

The build produces three full mod JAR variants:

- `matcha_flavoured_plus-1.0.0-curated-tabs-mod.jar` is the canonical
  modpack artifact: it hides the vanilla advancement tabs and keeps the
  separate Dungeons & Taverns tab.
- `matcha_flavoured_plus-1.0.0-clean-tabs-mod.jar` hides the vanilla
  advancement tabs without the Dungeons & Taverns overlay.
- `matcha_flavoured_plus-1.0.0-dungeons-and-taverns-compatible-mod.jar` keeps
  the vanilla advancement roots visible for broad compatibility.

The canonical variant moves Dungeons & Taverns' visible achievements into a
separate `Dungeons & Taverns` tab. The overlay keeps
D&T's original advancement IDs, criteria, rewards, and internal item IDs, so
the D&T mod remains responsible for its gameplay while Matcha owns the player-
facing progression layout.

The checked-in [compatibility manifest](modpack/matcha-flavoured-plus.manifest.json)
is the source of truth for the supported 26.2 baseline, integration policies,
and the pinned development-profile mod snapshot. It deliberately records the
current vanilla-ID compatibility aliases (including Netherite → Adamant)
without pretending that a display rename is a new registry item.

Apply the server-side integration settings to an explicitly selected profile
with a dry run first. The patcher changes only Waystones' warp rule and the
Chunk Loaders inactivity timeout, and stores a hash-named backup before writing:

```powershell
python tools/patch_profile_configs.py --profile "$env:MATCHA_PROFILE" --dry-run
python tools/patch_profile_configs.py --profile "$env:MATCHA_PROFILE"
```

Use the canonical `curated-tabs` variant for the Matcha Flavoured Plus
modpack. Choose exactly one variant for a profile.

When updating Dungeons & Taverns, regenerate its small advancement overlay
from the installed JAR before rebuilding:

```powershell
$env:MATCHA_PROFILE = "C:\path\to\Matcha Flavoured Plus Dev Build"
python tools/generate_dnt_advancement_overlay.py `
  "$env:MATCHA_PROFILE\mods\dungeons-and-taverns-5.3.0.jar"
```

## Install on a server

1. Install Fabric Loader and Fabric API for Minecraft 26.2.
2. Stop the server.
3. Copy exactly one Matcha mod JAR into the server's `mods` folder.
4. Start the server.
5. Install the same Matcha mod JAR, Fabric Loader, and Fabric API on each
   client.

The JAR contains both the gameplay datapack and the resource assets. Do not
also install the Lite datapack in the same world; that would load the gameplay
content twice.

## Shared gameplay

The Fabric edition includes the Lite behavior: managed multiplayer sleep,
instant Crystal Hearts, reworked food and hunger, custom progression and
equipment, blessing-based enchantments, enchanting-table book drops, fishing,
trades, mob changes, worldgen, and tutorials.

Loader-only work belongs here, including reliable interaction cancellation,
spawn-reason handling, and inventory/death-event handling when those features
are approved and implemented. A capability marked `FABRIC` in
[docs/capability-matrix.md](docs/capability-matrix.md) should not be advertised
as supported by Lite.

## Verification

```powershell
python tools/validate_advancements.py
python tools/validate_manifest.py
python -m unittest discover -s tests -v
python tools/build_distribution.py --include-mod
```

GitHub Actions also performs a Fabric runtime smoke test on `main`. Gameplay
and client rendering still need manual multiplayer verification before a
release is called fully gameplay-tested.

## Upstream and license

The upstream project is [Matcha Flavoured](https://modrinth.com/datapack/matcha-flavoured)
by Klei Wright (`klei_wright`). See [CREDITS.txt](CREDITS.txt) for attribution.

This derivative is shared under
[CC-BY-NC-SA-4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
