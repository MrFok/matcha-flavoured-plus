#!/usr/bin/env python3
"""Inventory and compare the recipes shipped by Matcha and active mod JARs.

This is intentionally a read-only audit.  It treats a recipe ID collision as a
hard problem, but treats two different recipes producing the same item as an
overlap report: that is often intentional for upgrades, storage integrations,
or ElytraTrims.  Run it against a profile before changing a progression rule:

    python tools/audit_recipe_inventory.py --mods-dir "...\\profile\\mods"
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Iterator
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RECIPE_MEMBER = re.compile(r"^data/([^/]+)/recipe/(.+)\.json$")


@dataclass(frozen=True)
class RecipeRecord:
    source: str
    namespace: str
    path: str
    recipe_id: str
    data: dict[str, Any]

    @property
    def recipe_type(self) -> str:
        return str(self.data.get("type", "<missing>"))


def parse_record(source: str, namespace: str, path: str, payload: bytes) -> RecipeRecord:
    data = json.loads(payload.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("recipe root must be an object")
    recipe_id = f"{namespace}:{path[:-5]}"
    return RecipeRecord(source, namespace, path, recipe_id, data)


def source_records(root: Path) -> Iterator[RecipeRecord]:
    for path in sorted((root / "data").glob("*/recipe/**/*.json")):
        relative = path.relative_to(root).as_posix()
        match = RECIPE_MEMBER.match(relative)
        if not match:
            continue
        yield parse_record(
            str(path.relative_to(root)),
            match.group(1),
            match.group(2) + ".json",
            path.read_bytes(),
        )


def jar_records(mods_dir: Path) -> Iterator[RecipeRecord]:
    for jar in sorted(mods_dir.glob("*.jar")):
        with zipfile.ZipFile(jar) as archive:
            for name in sorted(archive.namelist()):
                match = RECIPE_MEMBER.match(name)
                if match is None:
                    continue
                yield parse_record(
                    jar.name,
                    match.group(1),
                    match.group(2) + ".json",
                    archive.read(name),
                )


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def result_ids(recipe: dict[str, Any]) -> list[str]:
    result = recipe.get("result")
    if isinstance(result, dict) and isinstance(result.get("id"), str):
        return [result["id"]]
    if isinstance(result, list):
        return [entry["id"] for entry in result if isinstance(entry, dict) and isinstance(entry.get("id"), str)]
    results = recipe.get("results")
    if isinstance(results, list):
        return [entry["id"] for entry in results if isinstance(entry, dict) and isinstance(entry.get("id"), str)]
    return []


def input_signature(recipe: dict[str, Any]) -> str:
    without_output = {
        key: value
        for key, value in recipe.items()
        if key not in {"result", "results", "group", "show_notification"}
    }
    return canonical(without_output)


def walk_key(value: Any, key: str) -> Iterator[str]:
    if isinstance(value, dict):
        for name, child in value.items():
            if name == key and isinstance(child, str):
                yield child
            yield from walk_key(child, key)
    elif isinstance(value, list):
        for child in value:
            yield from walk_key(child, key)


def smithing_shape(recipe: dict[str, Any]) -> tuple[str, str, str, str] | None:
    if recipe.get("type") != "minecraft:smithing_transform":
        return None

    def shape(value: Any) -> str:
        return canonical(value)

    return (
        shape(recipe.get("template")),
        shape(recipe.get("base")),
        shape(recipe.get("addition")),
        ",".join(result_ids(recipe)),
    )


def print_group(title: str, groups: dict[Any, list[RecipeRecord]], limit: int = 40) -> None:
    interesting = [(key, value) for key, value in groups.items() if len(value) > 1]
    print(f"{title}: {len(interesting)}")
    for key, records in sorted(interesting, key=lambda item: str(item[0]))[:limit]:
        print(f"  {key}")
        for record in records:
            outputs = ",".join(result_ids(record.data)) or "<no result>"
            print(f"    - {record.source}: {record.recipe_id} -> {outputs}")
    if len(interesting) > limit:
        print(f"  ... {len(interesting) - limit} more")


def audit(
    records: list[RecipeRecord],
    assets_root: Path | None = None,
    namespace: str | None = None,
) -> int:
    if namespace is not None:
        records = [record for record in records if record.namespace == namespace]
        print(f"focused namespace: {namespace}")
    print(f"recipes: {len(records)}")
    print(f"sources: {len({record.source for record in records})}")
    print("by namespace:")
    for namespace, count in sorted(Counter(record.namespace for record in records).items()):
        print(f"  {namespace}: {count}")
    print("by recipe type:")
    for recipe_type, count in sorted(Counter(record.recipe_type for record in records).items()):
        print(f"  {recipe_type}: {count}")

    id_groups: dict[str, list[RecipeRecord]] = defaultdict(list)
    signature_groups: dict[str, list[RecipeRecord]] = defaultdict(list)
    exact_match_groups: dict[tuple[str, tuple[str, ...]], list[RecipeRecord]] = defaultdict(list)
    output_groups: dict[str, list[RecipeRecord]] = defaultdict(list)
    parse_errors: list[str] = []
    unqualified_smithing: list[RecipeRecord] = []
    for record in records:
        id_groups[record.recipe_id].append(record)
        signature_groups[input_signature(record.data)].append(record)
        exact_match_groups[(input_signature(record.data), tuple(result_ids(record.data)))].append(record)
        for output in result_ids(record.data):
            output_groups[output].append(record)
        if record.recipe_type == "minecraft:smithing_transform":
            for field in ("template", "base", "addition"):
                value = record.data.get(field)
                if isinstance(value, str) and ":" not in value and not value.startswith("#"):
                    unqualified_smithing.append(record)
                    break

    print_group("duplicate recipe IDs", id_groups)
    print_group("same inputs and outputs with multiple recipe IDs", exact_match_groups)
    print_group("same input signature with multiple recipe IDs", signature_groups)
    print_group("shared output IDs", output_groups, limit=20)

    smithing_groups: dict[tuple[str, str, str, str], list[RecipeRecord]] = defaultdict(list)
    for record in records:
        shape = smithing_shape(record.data)
        if shape is not None:
            smithing_groups[shape].append(record)
    print_group("identical smithing template/base/addition/result shapes", smithing_groups)

    print("elytra recipes:")
    for record in records:
        serialized = canonical(record.data).lower()
        if "elytra" in record.recipe_id.lower() or "elytra" in serialized:
            outputs = ",".join(result_ids(record.data)) or "<no result>"
            print(f"  - {record.source}: {record.recipe_id} -> {outputs}")

    if unqualified_smithing:
        print("unqualified smithing resource IDs:")
        for record in unqualified_smithing:
            print(f"  - {record.source}: {record.recipe_id}")

    if assets_root is not None:
        missing_models: dict[str, list[str]] = defaultdict(list)
        for record in records:
            for model in walk_key(record.data.get("result", {}), "minecraft:item_model"):
                namespace, _, path = model.partition(":")
                if not path:
                    namespace, path = "minecraft", namespace
                candidates = (
                    assets_root / "assets" / namespace / "items" / f"{path}.json",
                    assets_root / "assets" / namespace / "models" / "item" / f"{path}.json",
                )
                if not any(candidate.is_file() for candidate in candidates):
                    missing_models[model].append(record.recipe_id)
        print(f"item_model references without a source asset: {len(missing_models)}")
        for model, recipe_ids in sorted(missing_models.items())[:40]:
            print(f"  {model}")
            for recipe_id in recipe_ids[:6]:
                print(f"    - {recipe_id}")
        if len(missing_models) > 40:
            print(f"  ... {len(missing_models) - 40} more")

    errors = sum(1 for record in records if record.data is None)
    if errors:
        print(f"parse errors: {errors}")
    return 0 if not errors and not any(len(group) > 1 for group in id_groups.values()) else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mods-dir", type=Path, help="profile mods directory to inspect")
    parser.add_argument(
        "--source-root",
        type=Path,
        default=ROOT,
        help="Matcha source root (default: repository root)",
    )
    parser.add_argument(
        "--assets-root",
        type=Path,
        default=None,
        help="source root used for optional item_model asset checks",
    )
    parser.add_argument("--namespace", help="limit the report to one data namespace")
    parser.add_argument("--source-only", action="store_true", help="skip the source JAR/profile scan")
    parser.add_argument(
        "--profile-only",
        action="store_true",
        help="skip the Matcha source scan and inspect only --mods-dir JARs",
    )
    args = parser.parse_args(argv)

    if args.profile_only and args.mods_dir is None:
        parser.error("--profile-only requires --mods-dir")
    records = [] if args.profile_only else list(source_records(args.source_root))
    if args.mods_dir is not None and not args.source_only:
        records.extend(jar_records(args.mods_dir))
    return audit(records, args.assets_root, args.namespace)


if __name__ == "__main__":
    sys.exit(main())
