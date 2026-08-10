# 5IVE integration guardrails

These rules apply to every Matcha Flavoured Plus build, install, and debugging pass for the 5IVE modpack.

## Scope and system safety

- Target only `%APPDATA%\ModrinthApp\profiles\5IVE` unless the user explicitly names another profile.
- Never change Windows graphics preferences, GPU routing, drivers, registry values, power plans, or global Java settings unless the user explicitly requests that system-level change and a fresh log identifies the exact executable involved.
- GPU routing fixes must target the `Java Path` reported by the current launch. Modrinth can retain a high-performance preference for an older Java runtime while a newer Minecraft version launches a different `javaw.exe`. Back up `HKCU\Software\Microsoft\DirectX\UserGpuPreferences`, change only the exact current executable, and verify the selected adapter from a fresh client log.
- Treat third-party renderer warnings separately from adapter selection. Do not disable rendering or performance mods to compensate for an unverified GPU-routing theory.
- Do not change another Modrinth profile, a production world, or a server unless separately authorized.

## Installation safety

- Refuse to replace an active JAR while any `java` or `javaw` Minecraft process is running.
- Back up the exact active file before replacement and keep the backup outside the loader's active extension/path.
- Hash the built artifact and installed artifact with SHA-256 and require an exact match.
- Build selection must be deterministic. Prefer the explicit `MATCHA_PROFILE`; otherwise the development fallback may only select the `5IVE` folder or a single unambiguous profile.
- Never silently select the first profile returned by a directory listing.

## Build correctness

- Compile against the exact Minecraft `26.2` runtime and pin loader metadata to `=26.2`.
- Compile Java with `--release 21`.
- Recompile Java for every full mod build. Do not reuse source-only cached classes.
- Validate every Mixin field, method, descriptor, and injection callsite against the exact 26.2 bytecode before packaging.
- Fail the build when a required Matcha model, texture, loot-table reference, namespace, or recipe dependency is missing.
- Keep Matcha-owned data under `matcha_flavoured_plus`; use `minecraft` only for deliberate vanilla overrides.

## Runtime verification

- Automated tests are necessary but not sufficient. Every installed candidate must pass a fresh launch of `5IVE Dev Build`.
- The fresh client log must contain none of:
  - `InvalidMixinException`, `MixinApplyError`, `InjectionError`, or a Matcha Mixin transformation failure;
  - missing `bedrock_buster` or `warding_stone` models;
  - Matcha skeleton or ruin loot-table validation failures;
  - malformed Matcha pack metadata.
- Use `tools/runtime_smoke.py --log <latest.log> --log-only --require-gpu "NVIDIA GeForce RTX 5080"` for 5IVE client-log validation.
- Enter the duplicated test world for visible behavior checks. Confirm the HUD, recipes, item models, enchanting-table restrictions/counter, Silk Touch preservation, and ten-use break/drop behavior before calling those flows complete.

## Resource-pack policy

- Matcha's default is vanilla blocks and GUI, with Matcha item visuals and enchanted effects retained.
- Preserve the Vanilla Perfected identity layer unless the user explicitly removes it: Recolourful Containers owns container screens, qrafty's pack owns the capitalized font, Vanilla Perfected Panorama owns the title panorama, Vanilla Tweaks owns selected ambient vanilla refinements, and Dani's pack owns oxidizing copper-tool visuals.
- A vanilla-first Matcha asset policy does not authorize disabling the host modpack's independent cosmetic packs. Resolve an overlap at the conflicting asset path; do not remove an entire pack because it also contains unrelated UI, font, panorama, or animation assets.
- Preserve `Enchantment Outlines` unless the user explicitly asks to remove it.
- Classify log messages by owner before patching. Matcha, a third-party mod, and a third-party resource pack are separate fault domains.
- Do not disable or rewrite a third-party pack based only on a generic stack trace. Identify its exact archive and offending entry first.
- Any third-party archive edit must be minimal, backed up, and followed by a fresh resource reload proving the targeted warning changed.
- Apply the profile policy through `tools/patch_profile_resourcepacks.py`; do not recreate the disabled-pack list or ZIP edits by hand.
- Enchantment Outlines remains enabled. Its inherited placeholder particle textures are repaired to `#0`, which reuses each model's real item texture without changing the outline effect.
- Re-covered remains enabled. Only the six option sidecars that Respackopts cannot resolve are removed; the corresponding textures remain available.
- Keep Enchantment Outlines' oxidizing-copper compatibility definitions even while Dani's pack is disabled. Removing them causes Respackopts replacement failures; their remaining missing-model notices are inert compatibility registrations, not missing Matcha tool textures.
- Particle-only notices from vanilla internals, Tom's Storage, and Traveler's Backpack are not item-model failures. Do not rewrite mod JARs to silence them without a demonstrated visual defect.

## Regression lessons

- The earlier client crashes came from Mixin shadows/injections that were not valid for Minecraft 26.2. Exact bytecode contracts are now a build gate.
- The earlier texture and recipe confusion was worsened by overlapping resource packs and compatibility layers. Vanilla-first pack policy and explicit asset closure checks are now required.
- The first resource-pack cleanup overreached by moving five Vanilla Perfected identity packs out of the active directory. Pack-level removal erased unrelated font and UI behavior. Future cleanup must inventory asset ownership first, preserve the host pack's identity layer, and patch only demonstrated conflicting entries.
- Nearby dropped-item searches can accidentally mutate pre-existing entities. Capture entity IDs before block destruction and only modify newly spawned drops.
- Enchanting-table usage must fail closed when its block entity does not expose the Matcha counter; silently allowing unlimited use is not acceptable.
- A normal client boot does not prove gameplay behavior. Runtime claims must state exactly what was exercised and what remains untested.
- A warning-count reduction is not sufficient by itself. After every resource-pack rewrite, relaunch and compare all error categories; restore the SHA-backed prior archive immediately if a different category regresses.
- Do not infer GPU routing from FPS, backend choice, fullscreen state, or an old Java preference. The decisive evidence is the current log's `Java Path` paired with its `Using graphics device` line.
