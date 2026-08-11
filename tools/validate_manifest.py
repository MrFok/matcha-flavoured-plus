#!/usr/bin/env python3
"""Validate the checked-in Matcha Flavoured Plus compatibility manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "modpack" / "matcha-flavoured-plus.manifest.json"
EXPECTED_VISIBLE_ROOTS = {
    "matcha_flavoured_plus:main/tutorial/root",
    "matcha_flavoured_plus:main/hell/root",
    "matcha_flavoured_plus:main/end/root",
    "matcha_flavoured_plus:main/adventure/root",
}
EXPECTED_INTEGRATION_IDS = {
    "create": "create",
    "chunkloaders": "chunkloaders",
    "dungeons_and_taverns": "mr_dungeons_andtaverns",
    "easyshulkerboxes": "easyshulkerboxes",
    "fabric_api": "fabric-api",
    "toms_storage": "toms_storage",
    "travelersbackpack": "travelersbackpack",
    "veinminer": "veinminer",
    "veinminer_enchantment": "veinminer_enchantment",
    "waystones": "waystones",
}
EXPECTED_VANILLA_ROOTS = {
    "advancement/adventure",
    "advancement/end",
    "advancement/husbandry",
    "advancement/nether",
    "advancement/story",
}


def _archive_name(variant: str, kind: str) -> str:
    extension = "jar" if kind == "mod" else "zip"
    return f"matcha_flavoured_plus-1.0.0-{variant}-{kind}.{extension}"


def validate(path: Path = MANIFEST_PATH) -> list[str]:
    failures: list[str] = []
    try:
        manifest: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"{path}: invalid JSON: {error}"]

    project = manifest.get("project")
    if not isinstance(project, dict):
        failures.append("project must be an object")
    else:
        for field, expected in {
            "id": "matcha_flavoured_plus",
            "name": "Matcha Flavoured Plus",
            "version": "1.0.0",
            "minecraft": "26.2",
        }.items():
            if project.get(field) != expected:
                failures.append(f"project.{field} must be {expected!r}")
        loader = project.get("loader")
        if loader != {"id": "fabric", "version": "0.19.3"}:
            failures.append("project.loader must pin Fabric Loader 0.19.3")

    distribution = manifest.get("distribution")
    if not isinstance(distribution, dict):
        failures.append("distribution must be an object")
    else:
        if distribution.get("canonical_variant") != "curated-tabs":
            failures.append("distribution.canonical_variant must be curated-tabs")
        if distribution.get("server_config_patcher") != "tools/patch_profile_configs.py":
            failures.append("distribution.server_config_patcher must point to the guarded config patcher")
        if distribution.get("resource_pack_patcher") != "tools/patch_profile_resourcepacks.py":
            failures.append("distribution.resource_pack_patcher must point to the resource-pack policy tool")
        variants = distribution.get("variants")
        expected_variants = {"clean-tabs", "curated-tabs", "dungeons-and-taverns-compatible"}
        if not isinstance(variants, dict) or set(variants) != expected_variants:
            failures.append("distribution.variants must list exactly the three supported variants")
        else:
            for variant in expected_variants:
                for kind in ("datapack", "mod"):
                    expected = _archive_name(variant, kind)
                    if variants[variant].get(kind) != expected:
                        failures.append(f"distribution.variants.{variant}.{kind} must be {expected}")

    contract = manifest.get("integration_contract")
    if not isinstance(contract, dict):
        failures.append("integration_contract must be an object")
    else:
        if contract.get("matcha_namespace") != "matcha_flavoured_plus":
            failures.append("integration_contract.matcha_namespace is incorrect")
        required = contract.get("required_integrations")
        snapshot = manifest.get("modpack_snapshot", {}).get("mods", {})
        if not isinstance(required, dict):
            failures.append("integration_contract.required_integrations must be an object")
        elif not isinstance(snapshot, dict):
            failures.append("modpack_snapshot.mods must be an object")
        else:
            for name, expected_id in EXPECTED_INTEGRATION_IDS.items():
                if name not in required:
                    failures.append(f"required integration {name} is missing")
                    continue
                if expected_id not in snapshot:
                    failures.append(f"required integration {expected_id} is absent from the snapshot")
                elif snapshot[expected_id] != required[name]:
                    failures.append(
                        f"required integration {expected_id} version differs between contract and snapshot"
                    )

        policies = contract.get("policies")
        if not isinstance(policies, dict):
            failures.append("integration_contract.policies must be an object")
        else:
            if policies.get("automation_allowed") is not True:
                failures.append("automation_allowed must remain true")
            if policies.get("chunk_loader_inactive_timeout_days") != 7:
                failures.append("chunk_loader_inactive_timeout_days must remain 7")
            waystone = policies.get("waystone_warp_cost")
            if waystone != {
                "currency": "obol",
                "amount": 1,
                "registry_item": "minecraft:emerald",
                "rule_function": "item_cost",
                "experience_cost": 0,
            }:
                failures.append("waystone_warp_cost must be one Obol via minecraft:emerald item_cost with no XP cost")
            if policies.get("veinminer_requires_enchantment") is not True:
                failures.append("veinminer_requires_enchantment must remain true")
            enchanting = policies.get("enchanting_table")
            if not isinstance(enchanting, dict) or enchanting.get("books_only") is not True:
                failures.append("enchanting_table.books_only must remain true")
            elif enchanting.get("maximum_enchantments") != 10:
                failures.append("enchanting_table.maximum_enchantments must remain 10")
            advancement_policy = policies.get("advancements")
            if not isinstance(advancement_policy, dict):
                failures.append("advancements policy must be an object")
            else:
                if set(advancement_policy.get("visible_roots", [])) != EXPECTED_VISIBLE_ROOTS:
                    failures.append("advancement visible roots no longer match the four-tab contract")
                if set(advancement_policy.get("hidden_vanilla_roots", [])) != EXPECTED_VANILLA_ROOTS:
                    failures.append("hidden vanilla advancement roots no longer match the contract")

        aliases = contract.get("material_aliases")
        if not isinstance(aliases, dict) or aliases.get("minecraft:netherite") != "Adamant":
            failures.append("material_aliases must retain the netherite-to-Adamant alias")

    snapshot = manifest.get("modpack_snapshot")
    if not isinstance(snapshot, dict):
        failures.append("modpack_snapshot must be an object")
    else:
        mods = snapshot.get("mods")
        if not isinstance(mods, dict) or not mods:
            failures.append("modpack_snapshot.mods must be a non-empty object")
        else:
            if snapshot.get("loaded_mod_count") != 260:
                failures.append("modpack_snapshot.loaded_mod_count must match the pinned 260-entry launch snapshot")
            if snapshot.get("top_level_mod_count") != len(mods):
                failures.append("modpack_snapshot.top_level_mod_count does not match mods")
            if any(not isinstance(version, str) or not version for version in mods.values()):
                failures.append("every mod snapshot entry must have a non-empty version")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()
    failures = validate(args.manifest)
    if failures:
        print("Manifest validation failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("Matcha Flavoured Plus compatibility manifest is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
