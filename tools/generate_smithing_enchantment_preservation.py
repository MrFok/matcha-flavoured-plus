#!/usr/bin/env python3
"""Generate the datapack layer that preserves smithing enchantments.

Minecraft's smithing-transform result component patch replaces an entire
``minecraft:enchantments`` component.  The manifest captures the material
enchantments that used to be declared in those patches; generated recipe
advancements then apply only the missing levels after the transform has copied
the base item's original components.

Run this after adding or changing a smithing material enchantment:

    python tools/generate_smithing_enchantment_preservation.py

``--check`` is intentionally side-effect free and is used by the test suite.
``--bootstrap`` is only for creating a new manifest from recipes that still
contain their original enchantment result components.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECIPE_DIR = ROOT / "data" / "smithing_table" / "recipe"
DATA_ROOT = ROOT / "data" / "main"
MANIFEST_PATH = ROOT / "tools" / "smithing_enchantment_manifest.json"

ADVANCEMENT_DIR = DATA_ROOT / "advancement" / "smithing_enchantments"
FUNCTION_DIR = DATA_ROOT / "function" / "smithing_enchantments"
MODIFIER_DIR = DATA_ROOT / "item_modifier" / "smithing_enchantments"
PENDING_MARKER = "matcha_smithing_pending"

# 26.2 vanilla exclusive-set memberships, plus Matcha's custom damage member.
# A material enchantment is skipped whenever a different member of its set is
# already present.  This is intentionally preservation-first: existing player
# enchantments win over a material bonus rather than creating an invalid stack.
EXCLUSIVE_CONFLICTS = {
    "minecraft:fortune": ("minecraft:silk_touch",),
    "minecraft:silk_touch": ("minecraft:fortune",),
    "minecraft:smite": (
        "minecraft:bane_of_arthropods",
        "minecraft:breach",
        "minecraft:density",
        "minecraft:impaling",
        "minecraft:sharpness",
        "main:slaughter",
    ),
    "minecraft:blast_protection": (
        "minecraft:fire_protection",
        "minecraft:projectile_protection",
        "minecraft:protection",
    ),
    "minecraft:fire_protection": (
        "minecraft:blast_protection",
        "minecraft:projectile_protection",
        "minecraft:protection",
    ),
}

# Smithing output can be shift-clicked into any normal inventory slot or left
# on the cursor.  The equipment slots make a scheduled repair pass safe for an
# output that is moved before the next tick.
PLAYER_SLOTS = (
    *(f"inventory.{slot}" for slot in range(27)),
    *(f"hotbar.{slot}" for slot in range(9)),
    "weapon.offhand",
    "armor.head",
    "armor.chest",
    "armor.legs",
    "armor.feet",
    "player.cursor",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def render_json(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def render_recipe_json(value: Any) -> str:
    return json.dumps(value, indent="\t", ensure_ascii=False) + "\n"


def recipe_path(recipe_name: str) -> Path:
    return RECIPE_DIR / f"{recipe_name}.json"


def load_manifest() -> list[dict[str, Any]]:
    manifest = read_json(MANIFEST_PATH)
    if manifest.get("schema") != 1:
        raise ValueError("Unsupported smithing enchantment manifest schema")
    recipes = manifest.get("recipes")
    if not isinstance(recipes, list) or not recipes:
        raise ValueError("Smithing enchantment manifest has no recipes")
    names = [entry.get("recipe") for entry in recipes]
    if len(names) != len(set(names)) or any(not isinstance(name, str) for name in names):
        raise ValueError("Smithing enchantment manifest has duplicate or invalid recipe names")
    return recipes


def bootstrap_manifest() -> None:
    entries: list[dict[str, Any]] = []
    for path in sorted(RECIPE_DIR.glob("*.json")):
        recipe = read_json(path)
        result = recipe.get("result", {})
        components = result.get("components", {})
        enchantments = components.get("minecraft:enchantments")
        if enchantments is None:
            continue
        if not isinstance(enchantments, dict):
            raise ValueError(f"{path}: enchantments must be an object")
        entries.append(
            {
                "recipe": path.stem,
                "result_id": result["id"],
                "identity_components": {
                    key: value
                    for key, value in components.items()
                    if key != "minecraft:enchantments"
                },
                "enchantments": enchantments,
            }
        )

    if not entries:
        raise ValueError("No smithing result enchantments found to bootstrap")
    manifest = {
        "schema": 1,
        "description": "Source of truth for smithing material enchantment preservation.",
        "recipes": entries,
    }
    MANIFEST_PATH.write_text(render_json(manifest), encoding="utf-8")


def validate_manifest_recipe(entry: dict[str, Any]) -> None:
    name = entry["recipe"]
    path = recipe_path(name)
    if not path.is_file():
        raise ValueError(f"Manifest recipe is missing: {path}")
    recipe = read_json(path)
    if recipe.get("type") != "minecraft:smithing_transform":
        raise ValueError(f"{path}: expected smithing_transform")
    result = recipe.get("result", {})
    if result.get("id") != entry["result_id"]:
        raise ValueError(f"{path}: result id no longer matches the manifest")
    components = result.get("components", {})
    identity = {
        key: value
        for key, value in components.items()
        if key != "minecraft:enchantments"
    }
    normalized_identity = copy.deepcopy(identity)
    custom_data = normalized_identity.get("minecraft:custom_data")
    if (
        isinstance(custom_data, dict)
        and custom_data.get(PENDING_MARKER) == entry["recipe"]
    ):
        custom_data.pop(PENDING_MARKER)
        if not custom_data:
            normalized_identity.pop("minecraft:custom_data")
    if normalized_identity not in (
        entry["identity_components"],
        pending_identity_components(entry),
    ):
        raise ValueError(f"{path}: identity components no longer match the manifest")
    declared = components.get("minecraft:enchantments")
    if declared is not None and declared != entry["enchantments"]:
        raise ValueError(f"{path}: declared enchantments do not match the manifest")


def remove_enchantment_component_text(text: str) -> str:
    """Remove one formatted enchantment component without reformatting a recipe."""

    marker = '"minecraft:enchantments"'
    if text.count(marker) != 1:
        raise ValueError("Expected exactly one result enchantments component")
    marker_start = text.index(marker)
    line_start = text.rfind("\n", 0, marker_start) + 1
    value_start = text.index("{", marker_start + len(marker))

    depth = 0
    in_string = False
    escaped = False
    value_end = None
    for index in range(value_start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                value_end = index + 1
                break
    if value_end is None:
        raise ValueError("Could not locate the end of result enchantments component")
    if value_end >= len(text) or text[value_end] != ",":
        # The enchantments component is occasionally the last result component.
        # Remove the comma from the previous property instead of leaving a
        # trailing comma in the enclosing object.
        previous_comma = text.rfind(",", 0, line_start)
        if previous_comma < 0 or text[previous_comma + 1 : line_start].strip():
            raise ValueError("Expected a removable comma before final enchantments component")
        return text[:previous_comma] + text[value_end:]

    line_end = value_end + 1
    if text.startswith("\r\n", line_end):
        line_end += 2
    elif text.startswith("\n", line_end):
        line_end += 1
    else:
        raise ValueError("Expected a newline after result enchantments component")
    return text[:line_start] + text[line_end:]


def remove_recipe_enchantments(entry: dict[str, Any]) -> str:
    path = recipe_path(entry["recipe"])
    text = path.read_text(encoding="utf-8")
    recipe = read_json(path)
    components = recipe["result"].setdefault("components", {})
    declared = components.get("minecraft:enchantments")
    if declared is not None:
        if declared != entry["enchantments"]:
            raise ValueError(f"{path}: refusing to remove unexpected enchantments")
        text = remove_enchantment_component_text(text)
        recipe = json.loads(text)
        components = recipe["result"].setdefault("components", {})
    if not entry["enchantments"]:
        return text
    custom_data = components.get("minecraft:custom_data")
    if isinstance(custom_data, dict) and PENDING_MARKER in custom_data:
        if custom_data.pop(PENDING_MARKER) != entry["recipe"]:
            raise ValueError(f"{path}: unexpected pending marker")
        if not custom_data:
            components.pop("minecraft:custom_data")
    components["minecraft:item_name"] = pending_item_name(entry)
    return render_recipe_json(recipe)


def pending_item_name(entry: dict[str, Any]) -> dict[str, Any]:
    original = entry["identity_components"].get("minecraft:item_name")
    if original is None:
        raise ValueError(f"{entry['recipe']}: item_name is required for output scoping")
    return {
        "text": "",
        "extra": [
            copy.deepcopy(original),
            {
                "text": "",
                "insertion": f"{PENDING_MARKER}:{entry['recipe']}",
            },
        ],
    }


def pending_identity_components(entry: dict[str, Any]) -> dict[str, Any]:
    components = copy.deepcopy(entry["identity_components"])
    if not entry["enchantments"]:
        return components
    components["minecraft:item_name"] = pending_item_name(entry)
    return components


def enchantment_predicate(enchantment: str, levels: int | dict[str, int]) -> dict[str, Any]:
    return {
        "predicates": {
            "minecraft:enchantments": [
                {
                    "enchantments": enchantment,
                    "levels": levels,
                }
            ]
        }
    }


def min_level_modifier(enchantment: str, target_level: int) -> dict[str, Any]:
    """Return an idempotent modifier that raises, but never lowers, a level.

    ``set_enchantments.add`` is relative.  The chain first accepts any level at
    or above the target without changing it, then adds exactly the difference
    for every lower level, finally treating an absent enchantment as level zero.
    """

    if target_level < 1:
        raise ValueError(f"{enchantment}: expected positive target level")

    next_modifier: dict[str, Any] = {
        "function": "minecraft:set_enchantments",
        "enchantments": {enchantment: target_level},
        "add": True,
    }
    for current_level in range(target_level - 1, -1, -1):
        next_modifier = {
            "function": "minecraft:filtered",
            "item_filter": enchantment_predicate(enchantment, current_level),
            "modifier": {
                "function": "minecraft:set_enchantments",
                "enchantments": {enchantment: target_level - current_level},
                "add": True,
            },
            "on_fail": next_modifier,
        }
    return {
        "function": "minecraft:filtered",
        "item_filter": enchantment_predicate(enchantment, {"min": target_level}),
        "on_fail": next_modifier,
    }


def guarded_material_modifier(
    entry: dict[str, Any], enchantment: str, target_level: int
) -> dict[str, Any]:
    conflicts = EXCLUSIVE_CONFLICTS.get(enchantment, ())
    item_filter: dict[str, Any] = {
        "items": entry["result_id"],
        "components": pending_identity_components(entry),
    }
    modifier = min_level_modifier(enchantment, target_level)

    # Test conflicts by presence rather than testing every conflict at level
    # zero.  An unenchanted stack can omit the enchantments component entirely;
    # a chain of ``min: 1`` checks therefore safely falls through to the add
    # path for it, while any existing incompatible enchantment ends the chain
    # without mutating the stack.
    for conflict in reversed(conflicts):
        modifier = {
            "function": "minecraft:filtered",
            "item_filter": enchantment_predicate(conflict, {"min": 1}),
            "on_fail": modifier,
        }
    return {
        "function": "minecraft:filtered",
        "item_filter": item_filter,
        "modifier": modifier,
    }


def cleanup_pending_marker_modifier(entry: dict[str, Any]) -> dict[str, Any]:
    original_item_name = entry["identity_components"]["minecraft:item_name"]
    return {
        "function": "minecraft:filtered",
        "item_filter": {
            "items": entry["result_id"],
            "components": {
                "minecraft:item_name": pending_item_name(entry),
            },
        },
        "modifier": {
            "function": "minecraft:set_components",
            "components": {
                "minecraft:item_name": original_item_name,
            },
        },
    }


def render_modifier(entry: dict[str, Any]) -> str:
    modifiers = [
        guarded_material_modifier(entry, enchantment, level)
        for enchantment, level in entry["enchantments"].items()
    ]
    modifiers.append(cleanup_pending_marker_modifier(entry))
    return render_json(modifiers)


def render_advancement(entry: dict[str, Any]) -> str:
    name = entry["recipe"]
    advancement = {
        "criteria": {
            "crafted": {
                "trigger": "minecraft:recipe_crafted",
                "conditions": {"recipe_id": f"smithing_table:{name}"},
            }
        },
        "rewards": {"function": f"main:smithing_enchantments/{name}"},
    }
    return render_json(advancement)


def tag_name(entry: dict[str, Any]) -> str:
    return f"main.smithing_enchantments.{entry['recipe']}"


def render_reward_function(entry: dict[str, Any]) -> str:
    name = entry["recipe"]
    tag = tag_name(entry)
    return "\n".join(
        (
            f"advancement revoke @s only main:smithing_enchantments/{name}",
            f"tag @s add {tag}",
            f"schedule function main:smithing_enchantments/apply/{name} 1t replace",
            "",
        )
    )


def render_apply_function(entry: dict[str, Any]) -> str:
    name = entry["recipe"]
    tag = tag_name(entry)
    return "\n".join(
        (
            f"execute as @a[tag={tag}] run function main:smithing_enchantments/apply_player/{name}",
            f"tag @a[tag={tag}] remove {tag}",
            "",
        )
    )


def render_apply_player_function(entry: dict[str, Any]) -> str:
    modifier = f"main:smithing_enchantments/{entry['recipe']}"
    return "\n".join(
        [f"item modify entity @s {slot} {modifier}" for slot in PLAYER_SLOTS] + [""]
    )


def generated_files(entry: dict[str, Any]) -> dict[Path, str]:
    name = entry["recipe"]
    files = {
        recipe_path(name): remove_recipe_enchantments(entry),
    }
    # Empty result maps need no post-craft work.  Removing the component is
    # sufficient to stop the smithing transform from erasing the base item's
    # enchantments, and avoids a no-op scan after every such craft.
    if not entry["enchantments"]:
        return files
    files.update(
        {
            ADVANCEMENT_DIR / f"{name}.json": render_advancement(entry),
            FUNCTION_DIR / f"{name}.mcfunction": render_reward_function(entry),
            FUNCTION_DIR / "apply" / f"{name}.mcfunction": render_apply_function(entry),
            FUNCTION_DIR / "apply_player" / f"{name}.mcfunction": render_apply_player_function(entry),
            MODIFIER_DIR / f"{name}.json": render_modifier(entry),
        }
    )
    return files


def expected_files(entries: list[dict[str, Any]]) -> dict[Path, str]:
    files: dict[Path, str] = {}
    for entry in entries:
        files.update(generated_files(entry))
    return files


def write_generated(entries: list[dict[str, Any]]) -> None:
    for path, content in expected_files(entries).items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def check_generated(entries: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    expected = expected_files(entries)
    for path, content in expected.items():
        if not path.is_file():
            errors.append(f"missing generated file: {path.relative_to(ROOT)}")
        elif path.read_text(encoding="utf-8") != content:
            errors.append(f"stale generated file: {path.relative_to(ROOT)}")

    expected_names = {entry["recipe"] for entry in entries if entry["enchantments"]}
    generated_directories = (
        (ADVANCEMENT_DIR, "*.json"),
        (MODIFIER_DIR, "*.json"),
        (FUNCTION_DIR, "*.mcfunction"),
        (FUNCTION_DIR / "apply", "*.mcfunction"),
        (FUNCTION_DIR / "apply_player", "*.mcfunction"),
    )
    for directory, pattern in generated_directories:
        if not directory.exists():
            continue
        for path in directory.glob(pattern):
            if path.stem not in expected_names:
                errors.append(f"unexpected generated file: {path.relative_to(ROOT)}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    if args.bootstrap:
        bootstrap_manifest()

    entries = load_manifest()
    for entry in entries:
        validate_manifest_recipe(entry)

    if args.check:
        errors = check_generated(entries)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        return 0

    write_generated(entries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
