#!/usr/bin/env python3
"""Generate the small Dungeons & Taverns advancement compatibility overlay.

The overlay deliberately keeps D&T advancement IDs, criteria, and rewards. It
only changes the parent of visible D&T roots so they render in a Matcha-owned
tab, and fixes the English fallback for D&T's Netherite-themed achievement.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DNT_PREFIX = "data/nova_structures/advancement/"
DNT_ROOT = "nova_structures:root"
MATCHA_ROOT = "matcha_flavoured_plus:main/adventure/root"
ADAMANT_ADVANCEMENT = "nether/give_netherite_piglin_gold_armor.json"


def overlay_paths(archive: zipfile.ZipFile) -> list[str]:
    paths: list[str] = []
    for name in sorted(archive.namelist()):
        if not name.startswith(DNT_PREFIX) or not name.endswith(".json"):
            continue
        relative = name[len(DNT_PREFIX) :]
        definition = json.loads(archive.read(name))
        if relative == "root.json":
            paths.append(relative)
        elif relative == ADAMANT_ADVANCEMENT:
            paths.append(relative)
        elif definition.get("display") and str(definition.get("parent", "")).startswith("minecraft:"):
            paths.append(relative)
    if "root.json" not in paths:
        raise ValueError("Dungeons & Taverns root advancement is missing")
    return paths


def transform(relative: str, definition: dict) -> dict:
    if relative == "root.json":
        definition["parent"] = MATCHA_ROOT
    elif relative == ADAMANT_ADVANCEMENT:
        description = definition.get("display", {}).get("description", {})
        if description.get("fallback") == "Cause a Netherite Piglin to rethink their life choices.":
            description["fallback"] = "Cause an Adamant Piglin to rethink their life choices."
    elif definition.get("display") and str(definition.get("parent", "")).startswith("minecraft:"):
        definition["parent"] = DNT_ROOT
    return definition


def generate(source_jar: Path, output_root: Path) -> list[Path]:
    with zipfile.ZipFile(source_jar) as archive:
        paths = overlay_paths(archive)
        written: list[Path] = []
        for relative in paths:
            source_name = DNT_PREFIX + relative
            definition = json.loads(archive.read(source_name))
            destination = output_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(
                json.dumps(transform(relative, definition), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            written.append(destination)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_jar", type=Path, help="Dungeons & Taverns JAR to inspect")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data/nova_structures/advancement",
        help="overlay advancement directory",
    )
    args = parser.parse_args()
    for path in generate(args.source_jar, args.output):
        print(path)


if __name__ == "__main__":
    main()
