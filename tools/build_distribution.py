#!/usr/bin/env python3
"""Build deterministic Matcha Flavoured Plus distribution archives."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PROJECT_ID = "matcha_flavoured_plus"
VERSION = "1.0.0"
NAME = "Matcha Flavoured Plus"
LICENSE = "CC-BY-NC-SA-4.0"
REPOSITORY = "https://github.com/MrFok/matcha-flavoured-plus"
ISSUES = f"{REPOSITORY}/issues"
ROOT_FILES = ("pack.mcmeta", "pack.png", "CREDITS.txt")
JAVA_SOURCE_ROOT = ROOT / "src" / "main" / "java"
JAVA_RESOURCE_ROOT = ROOT / "src" / "main" / "resources"
JAVA_CACHE = ROOT / ".build" / "matcha-java-classes"
EPOCH = (1980, 1, 1, 0, 0, 0)
VANILLA_FIRST_MINECRAFT_ASSET_PREFIXES = (
    "assets/minecraft/items/",
    "assets/minecraft/models/item/",
    "assets/minecraft/textures/item/",
    "assets/minecraft/equipment/",
    "assets/minecraft/textures/entity/equipment/",
    "assets/minecraft/textures/trims/",
    "assets/minecraft/textures/misc/enchanted_glint_armor.png",
    "assets/minecraft/textures/misc/enchanted_glint_item.png",
    "assets/minecraft/textures/misc/enchanted_item_glint.png.mcmeta",
    "assets/minecraft/lang/",
    "assets/minecraft/sounds/",
    "assets/minecraft/sounds.json",
    "assets/minecraft/texts/",
	"assets/minecraft/textures/gui/sprites/hud/experience_bar_background.png",
	"assets/minecraft/textures/gui/sprites/hud/experience_bar_progress.png",
	"assets/minecraft/textures/gui/sprites/hud/food_empty.png",
	"assets/minecraft/textures/gui/sprites/hud/food_empty_hunger.png",
	"assets/minecraft/textures/gui/sprites/hud/food_full.png",
	"assets/minecraft/textures/gui/sprites/hud/food_full_hunger.png",
	"assets/minecraft/textures/gui/sprites/hud/food_half.png",
	"assets/minecraft/textures/gui/sprites/hud/food_half_hunger.png",
)
MATCHA_CUSTOM_BLOCK_ASSETS = frozenset(
    {
        "assets/minecraft/blockstates/bedrock_buster.json",
        "assets/minecraft/blockstates/warding_stone.json",
        "assets/minecraft/models/block/bedrock_buster.json",
        "assets/minecraft/models/block/warding_stone.json",
        "assets/minecraft/textures/block/bedrock_buster_bottom.png",
        "assets/minecraft/textures/block/bedrock_buster_side.png",
        "assets/minecraft/textures/block/bedrock_buster_top.png",
        "assets/minecraft/textures/block/warding_stone_side.png",
    }
)
OWNED_LOOT_TABLE_PREFIX = "data/minecraft/loot_table/kleis_items/"
OWNED_LOOT_TABLE_DESTINATION = "data/matcha_flavoured_plus/loot_table/main/"
OWNED_LOOT_REFERENCE = b"minecraft:kleis_items"
OWNED_LOOT_REPLACEMENT = b"matcha_flavoured_plus:main"
PACK_VARIANTS = {
    "clean-tabs": {
        "blocked_advancement_roots": (
            "advancement/adventure",
            "advancement/end",
            "advancement/husbandry",
            "advancement/nether",
            "advancement/story",
        )
    },
    "dungeons-and-taverns-compatible": {"blocked_advancement_roots": ()},
}


def archive_name(kind: str) -> str:
    extension = "jar" if kind.endswith("mod") else "zip"
    return f"{PROJECT_ID}-{VERSION}-{kind}.{extension}"


DEPRECATED_ARTIFACT_NAMES = (
    archive_name("datapack"),
    archive_name("mod"),
    *(
        archive_name(f"{variant}-{kind}")
        for variant in PACK_VARIANTS
        for kind in ("datapack", "mod")
    ),
    archive_name("original-resource-pack"),
    archive_name("vanilla-resource-pack"),
)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _java_tool(name: str) -> Path | None:
    candidates: list[Path] = []
    configured_home = os.environ.get("MATCHA_JAVA_HOME") or os.environ.get("JAVA_HOME")
    if configured_home:
        candidates.append(Path(configured_home) / "bin" / f"{name}.exe")
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.extend(
            Path(local_app_data).glob(f"Programs/Eclipse Adoptium/*/bin/{name}.exe")
        )
    which = shutil.which(name)
    if which:
        candidates.append(Path(which))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _runtime_paths() -> tuple[Path, list[Path]] | None:
    configured_minecraft = os.environ.get("MATCHA_MINECRAFT_JAR")
    configured_classpath = os.environ.get("MATCHA_COMPILE_CLASSPATH")
    if configured_minecraft and configured_classpath:
        minecraft = Path(configured_minecraft)
        dependencies = [
            Path(entry)
            for entry in configured_classpath.split(os.pathsep)
            if entry
        ]
        if minecraft.is_file() and dependencies and all(
            dependency.is_file() for dependency in dependencies
        ):
            return minecraft, dependencies
        return None

    app_data = os.environ.get("APPDATA")
    if not app_data:
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            app_data = str(Path(user_profile) / "AppData" / "Roaming")
    if not app_data:
        return None

    modrinth = Path(app_data) / "ModrinthApp"
    minecraft = Path(
        os.environ.get(
            "MATCHA_MINECRAFT_JAR",
            str(modrinth / "meta" / "versions" / "26.2" / "26.2.jar"),
        )
    )
    profiles_root = Path(os.environ.get("MATCHA_PROFILES_ROOT", str(modrinth / "profiles")))
    configured_profile = os.environ.get("MATCHA_PROFILE")
    def is_fabric_profile(candidate: Path) -> bool:
        processed = candidate / ".fabric" / "processedMods"
        return processed.is_dir() and any(
            processed.glob("fabric-events-interaction-v0-*.jar")
        )

    if configured_profile:
        configured = Path(configured_profile)
        profile = configured if is_fabric_profile(configured) else None
    else:
        discovered = (
            [candidate for candidate in sorted(profiles_root.iterdir()) if is_fabric_profile(candidate)]
            if profiles_root.is_dir()
            else []
        )
        preferred = profiles_root / "5IVE"
        if preferred in discovered:
            profile = preferred
        else:
            profile = discovered[0] if len(discovered) == 1 else None
    libraries = modrinth / "meta" / "libraries"
    if not minecraft.is_file() or profile is None or not libraries.is_dir():
        return None
    dependencies = [
        *sorted((profile / ".fabric" / "processedMods").glob("*.jar")),
        *sorted(libraries.rglob("*.jar")),
    ]
    return minecraft, dependencies


def _java_source_hash() -> str:
    digest = hashlib.sha256()
    for root in (JAVA_SOURCE_ROOT, JAVA_RESOURCE_ROOT):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file():
                digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
                digest.update(path.read_bytes())
    return digest.hexdigest()


MIXIN_RUNTIME_CONTRACTS = {
    "net.minecraft.world.inventory.AbstractContainerMenu": (
        "addDataSlot(net.minecraft.world.inventory.DataSlot)",
    ),
    "net.minecraft.world.inventory.EnchantmentMenu": (
        "private final net.minecraft.world.Container enchantSlots;",
        "private final net.minecraft.world.inventory.ContainerLevelAccess access;",
        "EnchantmentMenu(int, net.minecraft.world.entity.player.Inventory, net.minecraft.world.inventory.ContainerLevelAccess)",
        "slotsChanged(net.minecraft.world.Container)",
        "clickMenuButton(net.minecraft.world.entity.player.Player, int)",
        "lambda$clickMenuButton$0",
        "Player.experienceLevel:I",
        "Player.onEnchantmentPerformed:",
        "addSlot:",
    ),
    "net.minecraft.client.gui.screens.inventory.EnchantmentScreen": (
        "extractBackground(net.minecraft.client.gui.GuiGraphicsExtractor, int, int, float)",
        "extractRenderState(net.minecraft.client.gui.GuiGraphicsExtractor, int, int, float)",
        "LocalPlayer.experienceLevel:I",
    ),
    "net.minecraft.client.gui.Hud": (
        "extractFood(net.minecraft.client.gui.GuiGraphicsExtractor, net.minecraft.world.entity.player.Player, int, int)",
        "extractHotbarAndDecorations(net.minecraft.client.gui.GuiGraphicsExtractor, net.minecraft.client.DeltaTracker)",
        "nextContextualInfoState()",
        "MultiPlayerGameMode.hasExperience:()Z",
        "ContextualBar.extractExperienceLevel:",
    ),
    "net.minecraft.client.gui.contextualbar.ExperienceBar": (
        "extractBackground(net.minecraft.client.gui.GuiGraphicsExtractor, net.minecraft.client.DeltaTracker)",
        "extractRenderState(net.minecraft.client.gui.GuiGraphicsExtractor, net.minecraft.client.DeltaTracker)",
    ),
    "net.minecraft.world.level.block.entity.EnchantingTableBlockEntity": (
        "saveAdditional(net.minecraft.world.level.storage.ValueOutput)",
        "loadAdditional(net.minecraft.world.level.storage.ValueInput)",
    ),
    "net.minecraft.world.item.BlockItem": (
        "place(net.minecraft.world.item.context.BlockPlaceContext)",
        "ItemStack.consume:",
    ),
    "net.minecraft.world.level.block.Block": (
        "playerDestroy(net.minecraft.world.level.Level, net.minecraft.world.entity.player.Player, net.minecraft.core.BlockPos, net.minecraft.world.level.block.state.BlockState, net.minecraft.world.level.block.entity.BlockEntity, net.minecraft.world.item.ItemStack)",
    ),
}


def verify_mixin_runtime_contracts(minecraft: Path, javap: Path) -> None:
    """Fail the build when a Matcha mixin no longer matches Minecraft 26.2.

    Java compilation proves only that referenced types exist. Mixin injection
    points can still move or disappear and then crash during game bootstrap.
    Inspecting declarations plus bytecode call sites catches that class of
    regression before a candidate JAR reaches the Modrinth profile.
    """

    failures: list[str] = []
    for class_name, required_fragments in MIXIN_RUNTIME_CONTRACTS.items():
        result = subprocess.run(
            [str(javap), "-classpath", str(minecraft), "-p", "-s", "-c", class_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            failures.append(f"{class_name}: javap failed: {result.stderr.strip()}")
            continue
        missing = [fragment for fragment in required_fragments if fragment not in result.stdout]
        if missing:
            failures.append(f"{class_name}: missing {', '.join(repr(value) for value in missing)}")

    if failures:
        raise RuntimeError(
            "Matcha mixin runtime contract validation failed against "
            f"{minecraft}:\n" + "\n".join(failures)
        )


def compile_java_mod_entries() -> dict[str, bytes]:
    """Compile the small Fabric runtime layer and return archive entries.

    The datapack and resource-pack editions remain Java-free.  Only the full
    mod edition needs the local Minecraft/Fabric development jars; a hash-keyed
    cache lets tests and repeat builds reuse the already validated classes.
    """

    if not JAVA_SOURCE_ROOT.is_dir():
        return {}
    runtime = _runtime_paths()
    javac = _java_tool("javac")
    javap = _java_tool("javap")
    if runtime is None or javac is None or javap is None:
        raise RuntimeError(
            "Building the Matcha mod requires a local Java compiler and the Minecraft 26.2 "
            "Fabric compile classpath. Set MATCHA_JAVA_HOME, MATCHA_MINECRAFT_JAR, and "
            "MATCHA_COMPILE_CLASSPATH, or set MATCHA_PROFILE when they are not discoverable."
        )
    minecraft, dependencies = runtime
    verify_mixin_runtime_contracts(minecraft, javap)
    # Always compile full-mod candidates. A source-only cache previously reused
    # classes after Minecraft, Fabric, mappings, or the JDK changed, which can
    # produce a JAR that compiles nowhere near the runtime it is installed into.
    source_hash = _java_source_hash()
    with tempfile.TemporaryDirectory(prefix="matcha-java-") as temporary:
        output = Path(temporary) / "classes"
        output.mkdir()
        classpath = os.pathsep.join(
            [
                minecraft.as_posix(),
                *(path.as_posix() for path in dependencies),
            ]
        )
        sources = [path.as_posix() for path in sorted(JAVA_SOURCE_ROOT.rglob("*.java"))]
        arguments = [
            "--release",
            "21",
            "-encoding",
            "UTF-8",
            "-cp",
            classpath,
            "-d",
            output.as_posix(),
            *sources,
        ]
        argument_file = Path(temporary) / "javac.args"
        argument_file.write_text(
            "\n".join(f'"{argument.replace(chr(34), chr(92) + chr(34))}"' for argument in arguments),
            encoding="utf-8",
        )
        result = subprocess.run(
            [str(javac), f"@{argument_file}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "Matcha Fabric Java compilation failed:\n"
                + result.stdout
                + result.stderr
            )
        if JAVA_CACHE.exists():
            shutil.rmtree(JAVA_CACHE)
        JAVA_CACHE.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(output, JAVA_CACHE)
        (JAVA_CACHE / ".source-hash").write_text(source_hash + "\n", encoding="ascii")
        classes = JAVA_CACHE

    entries = {
        path.relative_to(classes).as_posix(): path.read_bytes()
        for path in classes.rglob("*.class")
    }
    entries.update(
        {
            path.relative_to(JAVA_RESOURCE_ROOT).as_posix(): path.read_bytes()
            for path in JAVA_RESOURCE_ROOT.rglob("*")
            if path.is_file()
        }
    )
    return entries


def source_entries(
    directories: tuple[str, ...],
    extra_root_files: tuple[str, ...] = (),
    root_overrides: dict[str, bytes] | None = None,
) -> dict[str, bytes]:
    entries = {
        name: (ROOT / name).read_bytes()
        for name in (*ROOT_FILES, *extra_root_files)
    }
    for directory in directories:
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file():
                entries[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    entries.update(root_overrides or {})
    return entries


def vanilla_first_assets(entries: dict[str, bytes]) -> dict[str, bytes]:
    """Keep Matcha's item presentation while yielding world/UI assets to vanilla.

    The official Matcha vanilla resource pack intentionally covers only the
    assets it changed in its original release.  The Plus source contains a
    much larger set of old block and GUI overrides, so merely enabling that
    pack still leaves those overrides in the built-in mod resources.  The
    default distribution therefore filters the Minecraft namespace at build
    time and retains item models/textures, equipment, language, sounds, and
    the custom glint textures only.
    """

    return {
        name: payload
        for name, payload in entries.items()
        if not name.startswith("assets/minecraft/")
        or name in MATCHA_CUSTOM_BLOCK_ASSETS
        or any(name.startswith(prefix) for prefix in VANILLA_FIRST_MINECRAFT_ASSET_PREFIXES)
    }


def move_owned_loot_tables(entries: dict[str, bytes]) -> dict[str, bytes]:
    """Package Matcha-owned leaf loot tables under Matcha's namespace.

    Vanilla loot-table overrides remain under ``data/minecraft`` because they
    replace vanilla entry points.  The reusable Matcha-owned tables do not,
    so they are relocated and all references are rewritten in the artifact.
    """

    rewritten: dict[str, bytes] = {}
    for name, payload in entries.items():
        if name.startswith(OWNED_LOOT_TABLE_PREFIX):
            name = OWNED_LOOT_TABLE_DESTINATION + name[len(OWNED_LOOT_TABLE_PREFIX) :]
        if name.startswith("data/"):
            payload = payload.replace(OWNED_LOOT_REFERENCE, OWNED_LOOT_REPLACEMENT)
        rewritten[name] = payload
    return rewritten


def pack_metadata(variant: str) -> bytes:
    metadata = json.loads((ROOT / "pack.mcmeta").read_text(encoding="utf-8"))
    blocked = metadata.setdefault("filter", {}).setdefault("block", [])
    advancement_roots = {
        path
        for config in PACK_VARIANTS.values()
        for path in config["blocked_advancement_roots"]
    }
    blocked[:] = [
        entry
        for entry in blocked
        if not (
            entry.get("namespace") == "minecraft"
            and entry.get("path") in advancement_roots
        )
    ]
    for path in PACK_VARIANTS[variant]["blocked_advancement_roots"]:
        blocked.append({"namespace": "minecraft", "path": path})
    return json_bytes(metadata)


def fabric_metadata() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "id": PROJECT_ID,
        "version": VERSION,
        "name": NAME,
        "description": "Matcha Flavoured Plus gameplay with vanilla world/UI assets and Matcha item visuals.",
        "license": LICENSE,
        "icon": "pack.png",
        "contact": {"homepage": REPOSITORY, "issues": ISSUES, "sources": REPOSITORY},
        "environment": "*",
        "entrypoints": {"main": ["com.mrfok.matcha.MatchaFlavouredPlus"]},
        "mixins": ["matcha_flavoured_plus.mixins.json"],
        "depends": {
            "fabric-api": "*",
            "fabric-resource-loader-v0": "*",
            "minecraft": "=26.2",
        },
    }


def quilt_metadata() -> dict[str, object]:
    return {
        "schema_version": 1,
        "quilt_loader": {
            "group": "com.mrfok",
            "id": PROJECT_ID,
            "version": VERSION,
            "metadata": {
                "name": NAME,
                "description": "Matcha Flavoured Plus gameplay with vanilla world/UI assets and Matcha item visuals.",
                "license": LICENSE,
                "icon": "pack.png",
                "contact": {"homepage": REPOSITORY, "issues": ISSUES, "sources": REPOSITORY},
            },
            "depends": [
                {"id": "minecraft", "versions": "=26.2"},
                {
                    "id": "quilt_resource_loader",
                    "versions": "*",
                    "unless": "fabric-resource-loader-v0",
                },
            ],
        },
    }


def forge_metadata(neoforge: bool) -> bytes:
    loader = "javafml" if neoforge else "lowcodefml"
    loader_version = "[1,)" if neoforge else "[40,)"
    return f'''modLoader="{loader}"
loaderVersion="{loader_version}"
license="{LICENSE}"
showAsResourcePack=false
issueTrackerURL="{ISSUES}"

[[mods]]
modId="{PROJECT_ID}"
version="{VERSION}"
displayName="{NAME}"
displayURL="{REPOSITORY}"
description="Matcha Flavoured Plus gameplay with vanilla world/UI assets and Matcha item visuals."
'''.encode("utf-8")


def write_archive(destination: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, entries[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(destination) as archive:
        corrupt_entry = archive.testzip()
    if corrupt_entry is not None:
        raise RuntimeError(f"archive validation failed for {destination}: {corrupt_entry}")


def build(output_dir: Path = DIST, include_mod: bool = False) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in DEPRECATED_ARTIFACT_NAMES:
        deprecated = output_dir / name
        if deprecated.is_file():
            deprecated.unlink()

    resource_pack = vanilla_first_assets(source_entries(("assets",)))
    artifacts = [output_dir / archive_name("resource-pack")]
    write_archive(artifacts[0], resource_pack)
    for variant in PACK_VARIANTS:
        root_overrides = {"pack.mcmeta": pack_metadata(variant)}
        datapack = move_owned_loot_tables(source_entries(("data",), root_overrides=root_overrides))
        datapack_destination = output_dir / archive_name(f"{variant}-datapack")
        write_archive(datapack_destination, datapack)
        artifacts.append(datapack_destination)
        if include_mod:
            mod = move_owned_loot_tables(
                vanilla_first_assets(source_entries(("data", "assets"), root_overrides=root_overrides))
            )
            mod.update(
                {
                    "fabric.mod.json": json_bytes(fabric_metadata()),
                    "quilt.mod.json": json_bytes(quilt_metadata()),
                    "META-INF/mods.toml": forge_metadata(False),
                    "META-INF/neoforge.mods.toml": forge_metadata(True),
                }
            )
            mod.update(compile_java_mod_entries())
            mod_destination = output_dir / archive_name(f"{variant}-mod")
            write_archive(mod_destination, mod)
            artifacts.append(mod_destination)
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DIST, help="artifact directory (default: dist)")
    parser.add_argument(
        "--include-mod",
        action="store_true",
        help="also build the full-edition mod JARs (main branch/release only)",
    )
    args = parser.parse_args()
    for artifact in build(args.output, include_mod=args.include_mod):
        print(artifact)


if __name__ == "__main__":
    main()
