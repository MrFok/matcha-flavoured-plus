#!/usr/bin/env python3
"""Build deterministic Matcha Flavoured Plus distribution archives."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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
EPOCH = (1980, 1, 1, 0, 0, 0)
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
    archive_name("original-resource-pack"),
    archive_name("vanilla-resource-pack"),
)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


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
        "description": "Matcha Flavoured Plus gameplay datapack and original visuals.",
        "license": LICENSE,
        "icon": "pack.png",
        "contact": {"homepage": REPOSITORY, "issues": ISSUES, "sources": REPOSITORY},
        "environment": "*",
        "depends": {"fabric-resource-loader-v0": "*", "minecraft": ">=26.2"},
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
                "description": "Matcha Flavoured Plus gameplay datapack and original visuals.",
                "license": LICENSE,
                "icon": "pack.png",
                "contact": {"homepage": REPOSITORY, "issues": ISSUES, "sources": REPOSITORY},
            },
            "depends": [
                {"id": "minecraft", "versions": ">=26.2"},
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
description="Matcha Flavoured Plus gameplay datapack and original visuals."
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

    resource_pack = source_entries(("assets",))
    artifacts = [output_dir / archive_name("resource-pack")]
    write_archive(artifacts[0], resource_pack)
    for variant in PACK_VARIANTS:
        root_overrides = {"pack.mcmeta": pack_metadata(variant)}
        datapack = source_entries(("data",), root_overrides=root_overrides)
        datapack_destination = output_dir / archive_name(f"{variant}-datapack")
        write_archive(datapack_destination, datapack)
        artifacts.append(datapack_destination)
        if include_mod:
            mod = source_entries(("data", "assets"), root_overrides=root_overrides)
            mod.update(
                {
                    "fabric.mod.json": json_bytes(fabric_metadata()),
                    "quilt.mod.json": json_bytes(quilt_metadata()),
                    "META-INF/mods.toml": forge_metadata(False),
                    "META-INF/neoforge.mods.toml": forge_metadata(True),
                }
            )
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
