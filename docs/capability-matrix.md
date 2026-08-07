# Capability matrix

This is the quick boundary map for issue planning. `DATAPACK` means it belongs
in `lite` first; `FABRIC` means it belongs in `main`; `NOT-DATAPACK` means a
datapack-only implementation would be unreliable or impossible.

| Capability | Tier | Current state |
| --- | --- | --- |
| Multiplayer sleep quorum | `DATAPACK` | Implemented in the shared sleep function; verify with two players. |
| Remove the vanilla enchanting-table recipe | `DATAPACK` | Implemented with the pack filter. |
| Drop 2–5 random enchanted books when the table is broken | `DATAPACK` | Implemented in the table loot table. |
| Prevent the enchanting-table screen from opening | `FABRIC` | Deferred; planned for a later `main`-only implementation. |
| Component-restricted Divine tool smithing upgrades | `FABRIC` | Reserved for `main`; vanilla smithing cannot inspect the required custom item data, so the recipes are omitted from `lite`. |
| Spawner-only loot suppression | `NOT-DATAPACK` / `FABRIC` | Not implemented; needs a spawn event that exposes the creation reason. |
| Deterministic death loss including nested storage | `FABRIC` | Design only; a datapack cannot safely account for every nested container. |
| Status-duration HUD flicker | `NOT-DATAPACK` | Client rendering change; outside the current vanilla resource-pack scope. |
| Automatic installation into an arbitrary vanilla Modrinth world | `NOT-DATAPACK` | A vanilla datapack still needs to be placed in that world's `datapacks` directory. |
| Custom item appearance and names | `RESOURCE-PACK` | Shared assets are shipped separately from the gameplay datapack. |
| Creator compatibility fixes | `DATAPACK` | Land on `upstream-fixes` first, then flow forward. |

The matrix is deliberately capability-based rather than branch-based: a safe
datapack feature is shared by `lite` and `main`, while a loader-only feature is
kept out of `lite` and clearly marked in the issue tracker.
