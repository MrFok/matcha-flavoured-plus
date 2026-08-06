# Branch and distribution responsibilities

The repository has three product lines with one-way dependency flow:

```text
upstream-fixes  ->  lite  ->  main
```

`upstream-fixes` stays close to the creator's project. `lite` is the
datapack-first Matcha Flavoured Plus edition. `main` is the full Fabric
edition, where features that need Java or loader events are allowed.

## Capability labels

Use these labels in issue descriptions, commits, and the feature matrix:

| Label | Meaning |
| --- | --- |
| `DATAPACK` | Works in the world datapack using functions, recipes, loot tables, advancements, tags, trades, or worldgen. |
| `RESOURCE-PACK` | Changes client visuals, models, textures, sounds, or language. It is separate from gameplay logic. |
| `FABRIC` | Needs Java code, a Fabric API event, or a client/server hook. It belongs on `main`. |
| `NOT-DATAPACK` | Cannot be implemented reliably by a datapack alone. Keep it documented rather than forcing a fragile approximation into `lite`. |
| `TOOLING` | Build, packaging, CI, or test-environment work; it is not a gameplay capability. |

A feature may have more than one label. For example, a custom item can be
`DATAPACK + RESOURCE-PACK`, while cancelling an enchanting-table screen is
`FABRIC`.

## `upstream-fixes`

This branch starts from the imported Matcha Flavoured 1.03 release and
contains only compatibility work and fixes for issues documented by the
original creator.

| Change | Included | Notes |
| --- | --- | --- |
| Minecraft 26.2 data/resource compatibility | Yes | Repairs current resource paths and schemas. |
| Sleep initialization without relog or `/reload` | Yes | Creates the objective before assigning constants. |
| Multiplayer Heart Container isolation | Yes | Preserves upstream automatic acquisition while targeting the correct player. |
| Sweet-berry effect for plain/fox-held berries | Yes | Keys behavior to `minecraft:sweet_berries`. |
| Smithing enchantment preservation | Yes | Preserves base enchantments and adds material minimums. |
| Feather Falling protection from ender-pearl damage | Yes | Uses an ender-pearl-specific damage-type tag. |
| Spawner-origin loot suppression | No | Still unresolved and not reliable with datapack-only information. |
| Automatic vanilla Modrinth world installation | No | Vanilla datapacks still require a target world's `datapacks` directory. |
| Matcha Flavoured Plus custom content | No | Intentionally excluded. |

Never merge Plus-only changes back into this branch. When the creator ships a
fix, land or adapt it here first, then merge it forward into `lite` and `main`.

## `lite`

This is the no-mod edition. It contains Plus changes that remain within the
datapack/resource-pack model and must not contain Java entrypoints or a Fabric
API dependency.

Typical `lite` content includes:

- functions, recipes, loot tables, advancements, tags, trades, and worldgen;
- datapack-safe balance and progression changes;
- a separate resource-pack archive for the custom visuals.

The canonical vanilla installation artifacts are ZIP files: one gameplay
datapack ZIP and one resource-pack ZIP. A `.jar` extension does not give a
vanilla datapack new capabilities, so a JAR should not be advertised as the
vanilla installation format. The JAR convenience belongs to the Fabric
edition described below. The distribution builder defaults to this Lite output;
`--include-mod` is reserved for the full `main` release.

Some behavior will intentionally differ between `lite` and `main`. For
example, `lite` can remove the enchanting-table recipe and replace its block
loot, but it cannot cancel the client's right-click interaction before the
vanilla screen opens. That cancellation is a `FABRIC` feature.

## `main`

This is the full Matcha Flavoured Plus Fabric edition and the repository's
default integration branch. It should consume `lite` changes rather than
reimplementing them, then add Java-backed features that are impossible or
unreliable in a datapack.

The Fabric JAR may include:

- all shared datapack content and resource assets;
- Fabric entrypoints and server/client event hooks;
- reliable spawn-reason handling, inventory/death handling, interaction
  cancellation, and other loader-level behavior when those features are
  approved and tested.

The current Java work is Fabric-specific. Quilt, Forge, and NeoForge metadata
must not be treated as support until each loader has a real implementation and
runtime test.

Calling this branch the **Fabric edition** or **full mod** is more precise than
calling it a modpack. A modpack normally means a collection of separate mods;
this repository currently produces one mod containing the datapack and its
resources.

## Development flow

1. Import and verify creator fixes on `upstream-fixes`.
2. Merge `upstream-fixes` into `lite`.
3. Implement every `DATAPACK` feature on `lite` first and build the vanilla ZIPs.
4. Merge `lite` into `main`.
5. Implement only `FABRIC` features on `main`, with Fabric runtime tests.
6. Release the vanilla ZIPs from `lite` and the Fabric JAR from `main`; use
   tags/releases for versions instead of creating a new branch per release.

Do not merge `main` back into `upstream-fixes`, and do not use a Fabric-only
workaround to claim that the `lite` edition supports a capability it cannot
actually provide.
