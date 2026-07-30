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


def archive_name(kind: str) -> str:
    extension = "jar" if kind == "mod" else "zip"
    return f"{PROJECT_ID}-{VERSION}-{kind}.{extension}"


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def source_entries(directories: tuple[str, ...]) -> dict[str, bytes]:
    entries = {name: (ROOT / name).read_bytes() for name in ROOT_FILES}
    for directory in directories:
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file():
                entries[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    return entries


def fabric_metadata() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "id": PROJECT_ID,
        "version": VERSION,
        "name": NAME,
        "description": "Matcha Flavoured Plus datapack and resource pack.",
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
                "description": "Matcha Flavoured Plus datapack and resource pack.",
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
description="Matcha Flavoured Plus datapack and resource pack."
'''.encode("utf-8")


def write_archive(destination: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, entries[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(output_dir: Path = DIST) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    datapack = source_entries(("data",))
    resource_pack = source_entries(("assets",))
    mod = source_entries(("data", "assets"))
    mod.update(
        {
            "fabric.mod.json": json_bytes(fabric_metadata()),
            "quilt.mod.json": json_bytes(quilt_metadata()),
            "META-INF/mods.toml": forge_metadata(False),
            "META-INF/neoforge.mods.toml": forge_metadata(True),
        }
    )
    artifacts = []
    for kind, entries in (("datapack", datapack), ("resource-pack", resource_pack), ("mod", mod)):
        destination = output_dir / archive_name(kind)
        write_archive(destination, entries)
        artifacts.append(destination)
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DIST, help="artifact directory (default: dist)")
    args = parser.parse_args()
    for artifact in build(args.output):
        print(artifact)


if __name__ == "__main__":
    main()
