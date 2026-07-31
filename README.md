# Matcha Flavoured Plus

A preference-driven derivative of [Matcha Flavoured](https://modrinth.com/datapack/matcha-flavoured) for Minecraft: Java Edition.

The goal of this repository is to build on the original datapack while making deliberate balance, usability, compatibility, and quality-of-life changes. The original Matcha textures are the recommended texture choice; planned deviations and verified defects are tracked as GitHub issues before implementation.

## Upstream

- Original project: [Matcha Flavoured on Modrinth](https://modrinth.com/datapack/matcha-flavoured)
- Original creator: Klei Wright (`klei_wright`)
- Baseline represented here: Matcha Flavoured 1.03 for Minecraft 26.2

See [CREDITS.txt](CREDITS.txt) for the upstream attribution and acknowledgements included with the pack.

## Installation

Build the distribution files with `python tools/build_distribution.py`. The generated files are in `dist/`.

### Modrinth App / launcher

Upload only `matcha_flavoured_plus-1.0.0-mod.jar` to the profile. It contains
the gameplay datapack and the Original Matcha resource assets, including the
Divine item visuals. No resource-pack installation or in-game toggle is needed.

Fabric 26.2 with Fabric API is runtime-verified. Quilt, Forge, and NeoForge
metadata is included, but those launch paths remain experimental until they are
tested in-game.

### Vanilla Minecraft

Install the gameplay archive and texture archive manually:

1. Put `matcha_flavoured_plus-1.0.0-datapack.zip` in the target world's `datapacks` folder.
2. Put `matcha_flavoured_plus-1.0.0-resource-pack.zip` in the client's `resourcepacks` folder.
3. Enable **Matcha Flavoured Plus**.

The Modrinth App can install the self-contained mod JAR directly. The standalone
archives remain available for vanilla-world installation.

## Textures

The repository's root `assets/` tree is the only built texture source. The mod JAR
and standalone resource pack contain the same Original Matcha assets. There is no
Original/Vanilla style selector or generated Vanilla Flavoured pack.

## Verification

The distribution builder uses only Python's standard library. Run:

```powershell
python -m unittest discover -s tests -v
python tools/build_distribution.py
```

Tests validate archive layout, content boundaries, metadata, JSON, exclusions, and deterministic rebuild hashes. They do not replace in-game Minecraft testing of gameplay behavior.

## Compatibility notes

- Dungeons & Taverns can be enabled. Matcha no longer filters the vanilla advancement roots that its advancements use.
- The experience bar is intentionally transparent. AppleSkin can still draw its own hunger HUD overlays; disable AppleSkin or its HUD overlays if you want Matcha's hidden hunger bar.

## License

This derivative is shared under the same
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/)
license as the upstream project.

You must provide attribution, may not use the work commercially, and must distribute adaptations under the same license.
