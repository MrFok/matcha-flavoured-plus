#!/usr/bin/env python3
"""Apply the reproducible, minimal resource-pack policy for the 5IVE profile."""

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


DEFAULT_PROFILE = (
    Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    / "ModrinthApp"
    / "profiles"
    / "5IVE"
)

PRESERVED_PACKS = (
    "Dani's Oxidizing Copper Tools.zip",
    "qrafty's-capitalized-font-3.5.zip",
    "Recolourful Containers 3.1.3 (1.19.4+).zip",
    "Vanilla Perfected Panorama.zip",
    "Vanilla Tweaks (VP Default).zip",
)

DISABLED_PACKS: tuple[str, ...] = ()

METADATA_PACKS = (
    "Ben's Bundles 1.4.zip",
    "§4Drodi's Blazes FA [V1.2].zip",
    "§9Drodi's Illagers x FA [v5.2].zip",
)

RECOVERED_BROKEN_OPTIONS = frozenset(
    {
        "assets/carl/textures/item/alternative/depth_strider_old.png.rpo",
        "assets/carl/textures/item/alternative/quick_charge_alt1.png.rpo",
        "assets/carl/textures/item/alternative/respiration_old.png.rpo",
        "assets/carl/textures/item/not_animated/respiration.png.rpo",
        "assets/carl/textures/item/not_animated/soul_speed.png.rpo",
        "assets/carl/textures/item/not_animated/vanishing_curse.png.rpo",
    }
)

OUTLINE_PARENT_FALLBACKS = {
    "assets/minecraft/models/item/firstperson/compass/enchanted_compass.json":
        "minecraft:item/compass/e_00",
    "assets/minecraft/models/item/thirdperson/compass/enchanted_compass.json":
        "minecraft:item/compass/e_00",
    "assets/minecraft/models/item/firstperson/hoe/enchanted_hoe.json":
        "minecraft:item/wooden/hoe",
    "assets/minecraft/models/item/firstperson/shovel/enchanted_shovel.json":
        "minecraft:item/wooden/shovel",
    "assets/minecraft/models/item/firstperson/sword/enchanted_sword.json":
        "minecraft:item/wooden/sword",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def minecraft_is_running() -> bool:
    if os.name != "nt":
        return False
    for image in ("javaw.exe", "java.exe"):
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
        )
        if image.casefold() in result.stdout.casefold():
            return True
    return False


def is_macos_junk(name: str) -> bool:
    parts = name.replace("\\", "/").split("/")
    return "__MACOSX" in parts or ".DS_Store" in parts or any(
        part.startswith("._") for part in parts
    )


def patch_pack_metadata(raw: bytes) -> bytes:
    payload = json.loads(raw.decode("utf-8-sig"))
    pack = payload.get("pack", {})
    supported = pack.get("supported_formats")
    if supported is None or (
        "min_format" in pack and "max_format" in pack
    ):
        return raw
    if isinstance(supported, dict):
        minimum = supported.get("min_inclusive", supported.get("min"))
        maximum = supported.get("max_inclusive", supported.get("max"))
    elif isinstance(supported, list) and len(supported) == 2:
        minimum, maximum = supported
    else:
        minimum = maximum = supported
    pack["min_format"] = minimum
    pack["max_format"] = maximum
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def patch_outline_model(name: str, raw: bytes) -> bytes:
    payload = json.loads(raw.decode("utf-8-sig"))
    textures = payload.get("textures")
    if not isinstance(textures, dict):
        return raw

    changed = False
    if name.endswith("/book/book_outline.json") and textures.get("1"):
        if textures.get("particle") != "#1":
            textures["particle"] = "#1"
            changed = True
    fallback = OUTLINE_PARENT_FALLBACKS.get(name)
    if fallback is not None and textures.get("0") != fallback:
        textures["0"] = fallback
        changed = True

    particle = textures.get("particle")
    known_bad_particle = (
        fallback is not None
        or (
            isinstance(particle, str)
            and particle.startswith("minecraft:item/copper/enchanted_")
            and particle.endswith("_axe")
        )
        or (
            "assets/minecraft/models/item/oxidizingcopper/" in name
            and isinstance(particle, str)
        )
    )
    if known_bad_particle and textures.get("0") and particle != "#0":
        textures["particle"] = "#0"
        changed = True

    if not changed:
        return raw
    return (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def transform_entry(pack_name: str, name: str, raw: bytes) -> bytes | None:
    normalized = name.replace("\\", "/")
    if is_macos_junk(normalized):
        return None
    if pack_name == "Re-covered.zip" and normalized in RECOVERED_BROKEN_OPTIONS:
        return None
    if pack_name in METADATA_PACKS and normalized == "pack.mcmeta":
        return patch_pack_metadata(raw)
    if (
        pack_name == "Enchantment Outlines.zip"
        and normalized.startswith("assets/minecraft/models/item/")
        and normalized.endswith(".json")
    ):
        return patch_outline_model(normalized, raw)
    return raw


def rewrite_pack(path: Path, backup_root: Path, dry_run: bool) -> bool:
    with zipfile.ZipFile(path, "r") as source:
        entries: list[tuple[zipfile.ZipInfo, bytes]] = []
        changed = False
        for info in source.infolist():
            raw = source.read(info.filename)
            updated = transform_entry(path.name, info.filename, raw)
            if updated is None:
                changed = True
                continue
            changed |= updated != raw
            entries.append((info, updated))

    if not changed or dry_run:
        return changed

    original_hash = sha256(path)
    backup_root.mkdir(parents=True, exist_ok=True)
    backup = backup_root / f"{original_hash[:16]}-{path.name}"
    if not backup.exists():
        shutil.copy2(path, backup)

    with tempfile.NamedTemporaryFile(
        prefix=f".{path.stem}-", suffix=".zip", dir=path.parent, delete=False
    ) as temporary:
        temporary_path = Path(temporary.name)
    try:
        with zipfile.ZipFile(temporary_path, "w") as target:
            for info, raw in entries:
                cloned = zipfile.ZipInfo(info.filename, info.date_time)
                cloned.compress_type = info.compress_type
                cloned.comment = info.comment
                cloned.extra = info.extra
                cloned.internal_attr = info.internal_attr
                cloned.external_attr = info.external_attr
                cloned.create_system = info.create_system
                target.writestr(cloned, raw)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)
    return True


def ensure_selected_packs(profile: Path, backup_root: Path, dry_run: bool) -> bool:
    options = profile / "options.txt"
    lines = options.read_text(encoding="utf-8").splitlines(keepends=True)
    prefix = "resourcePacks:"
    line_index = next(
        (index for index, line in enumerate(lines) if line.startswith(prefix)),
        None,
    )
    if line_index is None:
        raise ValueError(f"resourcePacks entry not found in {options}")

    newline = "\r\n" if lines[line_index].endswith("\r\n") else "\n"
    original_selected = json.loads(
        lines[line_index][len(prefix):].rstrip("\r\n")
    )
    selected = list(original_selected)
    restored = {name: f"file/{name}" for name in PRESERVED_PACKS}
    selected = [pack for pack in selected if pack not in restored.values()]

    def insert_after(anchor: str, pack: str) -> None:
        index = selected.index(anchor) + 1 if anchor in selected else len(selected)
        selected.insert(index, pack)

    def insert_before(anchor: str, pack: str) -> None:
        index = selected.index(anchor) if anchor in selected else len(selected)
        selected.insert(index, pack)

    insert_after(
        "continuity:glass_pane_culling_fix",
        restored["Recolourful Containers 3.1.3 (1.19.4+).zip"],
    )
    insert_after(
        restored["Recolourful Containers 3.1.3 (1.19.4+).zip"],
        restored["Vanilla Tweaks (VP Default).zip"],
    )
    insert_after(
        "file/Enchantment Outlines.zip",
        restored["Dani's Oxidizing Copper Tools.zip"],
    )
    insert_before(
        "elytratrails:arrowtrails",
        restored["Vanilla Perfected Panorama.zip"],
    )
    selected.append(restored["qrafty's-capitalized-font-3.5.zip"])

    if selected == original_selected:
        return False
    if dry_run:
        return True

    updated = prefix + json.dumps(
        selected, ensure_ascii=True, separators=(",", ":")
    ) + newline

    backup_root.mkdir(parents=True, exist_ok=True)
    original_hash = sha256(options)
    backup = backup_root / f"{original_hash[:16]}-options.txt"
    if not backup.exists():
        shutil.copy2(options, backup)
    lines[line_index] = updated
    options.write_text("".join(lines), encoding="utf-8", newline="")
    return True


def apply(profile: Path, dry_run: bool = False) -> list[str]:
    resourcepacks = profile / "resourcepacks"
    if not resourcepacks.is_dir():
        raise FileNotFoundError(f"Resource-pack directory not found: {resourcepacks}")
    if not dry_run and minecraft_is_running():
        raise RuntimeError("Refusing to patch resource packs while Java/Minecraft is running")

    disabled = profile / "resourcepacks-disabled-by-matcha"
    backup_root = disabled / "profile-patch-backups"
    changes: list[str] = []

    for name in PRESERVED_PACKS:
        source = disabled / name
        destination = resourcepacks / name
        if source.exists():
            changes.append(f"restore {name}")
            if not dry_run:
                if destination.exists():
                    raise FileExistsError(
                        f"Refusing to overwrite enabled pack: {destination}"
                    )
                shutil.move(source, destination)

    missing_preserved = [
        name
        for name in PRESERVED_PACKS
        if not (resourcepacks / name).exists() and not (disabled / name).exists()
    ]
    if missing_preserved:
        raise FileNotFoundError(
            "Required Vanilla Perfected identity pack(s) missing: "
            + ", ".join(missing_preserved)
        )

    for name in DISABLED_PACKS:
        source = resourcepacks / name
        destination = disabled / name
        if source.exists():
            changes.append(f"disable {name}")
            if not dry_run:
                disabled.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    raise FileExistsError(f"Refusing to overwrite disabled pack: {destination}")
                shutil.move(source, destination)

    if ensure_selected_packs(profile, backup_root, dry_run):
        changes.append("restore Vanilla Perfected resource-pack selection")

    patch_names = (
        *METADATA_PACKS,
        *PRESERVED_PACKS,
        "Enchantment Outlines.zip",
        "Re-covered.zip",
        "Weskerson's Torches.zip",
    )
    for name in patch_names:
        path = resourcepacks / name
        if path.exists() and rewrite_pack(path, backup_root, dry_run):
            changes.append(f"patch {name}")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    changes = apply(args.profile, args.dry_run)
    for change in changes:
        print(change)
    print(f"{len(changes)} change(s) {'required' if args.dry_run else 'applied'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
