import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "smithing_enchantment_generator",
    ROOT / "tools" / "generate_smithing_enchantment_preservation.py",
)
generator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(generator)


EXPECTED_ENCHANTED_SMITHING_RECIPES = {
    "adamant_axe",
    "adamant_boots",
    "adamant_chestplate",
    "adamant_claymore",
    "adamant_dolabra",
    "adamant_helmet",
    "adamant_hoe",
    "adamant_leggings",
    "adamant_mattock",
    "adamant_pickaxe",
    "adamant_shovel",
    "adamant_spear",
    "adamant_sword",
    "amber_earrings",
    "bronze_boots",
    "bronze_chestplate",
    "bronze_elytra",
    "bronze_helmet",
    "bronze_leggings",
    "bronze_spear",
    "bronze_sword",
    "butcher_knife",
    "electrum_axe",
    "electrum_boots",
    "electrum_chestplate",
    "electrum_dolabra",
    "electrum_helmet",
    "electrum_hoe",
    "electrum_leggings",
    "electrum_mattock",
    "electrum_pickaxe",
    "electrum_shovel",
    "electrum_spear",
    "electrum_sword",
    "gilded_leather_boots",
    "lesser_warding_shield",
    "shakudo_axe",
    "shakudo_boots",
    "shakudo_chestplate",
    "shakudo_dolabra",
    "shakudo_helmet",
    "shakudo_hoe",
    "shakudo_leggings",
    "shakudo_mattock",
    "shakudo_pickaxe",
    "shakudo_shovel",
    "shakudo_spear",
    "shakudo_sword",
    "silver_sword",
    "steel_boots",
    "steel_chestplate",
    "steel_helmet",
    "steel_leggings",
    "steel_spear",
    "warding_shield",
    "warding_sword",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def levels_match(levels, level):
    if isinstance(levels, int):
        return level == levels
    if "min" in levels and level < levels["min"]:
        return False
    if "max" in levels and level > levels["max"]:
        return False
    return True


def apply_modifier(modifier, levels):
    """Evaluate the generated modifier subset for static min-level checks."""

    if isinstance(modifier, list):
        for entry in modifier:
            apply_modifier(entry, levels)
        return

    function = modifier["function"]
    if function == "minecraft:set_enchantments":
        assert modifier["add"] is True
        for enchantment, delta in modifier["enchantments"].items():
            levels[enchantment] = levels.get(enchantment, 0) + delta
        return

    if function != "minecraft:filtered":
        raise AssertionError(f"Unexpected generated modifier function: {function}")

    predicates = modifier["item_filter"].get("predicates", {}).get(
        "minecraft:enchantments", []
    )
    matches = all(
        levels_match(predicate["levels"], levels.get(predicate["enchantments"], 0))
        for predicate in predicates
    )
    if matches:
        if "modifier" in modifier:
            apply_modifier(modifier["modifier"], levels)
    elif "on_fail" in modifier:
        apply_modifier(modifier["on_fail"], levels)


class SmithingEnchantmentPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = generator.load_manifest()
        cls.by_name = {entry["recipe"]: entry for entry in cls.entries}

    def test_generator_output_is_current(self):
        self.assertEqual(generator.main(["--check"]), 0)

    def test_manifest_covers_the_full_baseline(self):
        self.assertEqual(set(self.by_name), EXPECTED_ENCHANTED_SMITHING_RECIPES)
        self.assertEqual(len(self.entries), 56)
        self.assertEqual(
            {entry["recipe"] for entry in self.entries if not entry["enchantments"]},
            {
                "bronze_boots",
                "bronze_chestplate",
                "bronze_elytra",
                "bronze_helmet",
                "bronze_leggings",
                "steel_spear",
            },
        )

    def test_recipe_patches_no_longer_replace_enchantments(self):
        for path in sorted((ROOT / "data/matcha_flavoured_plus/recipe/smithing_table").glob("*.json")):
            with self.subTest(recipe=path.stem):
                recipe = read_json(path)
                self.assertNotIn(
                    "minecraft:enchantments",
                    recipe.get("result", {}).get("components", {}),
                )
                if path.stem in {
                    entry["recipe"] for entry in self.entries if entry["enchantments"]
                }:
                    entry = self.by_name[path.stem]
                    self.assertEqual(
                        recipe["result"]["components"]["minecraft:item_name"],
                        generator.pending_item_name(entry),
                    )
                    self.assertNotIn(
                        generator.PENDING_MARKER,
                        recipe["result"]["components"].get(
                            "minecraft:custom_data", {}
                        ),
                    )

    def test_nonempty_material_maps_have_repeatable_craft_handlers(self):
        for entry in self.entries:
            name = entry["recipe"]
            advancement_path = (
                ROOT / f"data/matcha_flavoured_plus/advancement/main/smithing_enchantments/{name}.json"
            )
            modifier_path = ROOT / f"data/matcha_flavoured_plus/item_modifier/main/smithing_enchantments/{name}.json"
            reward_path = ROOT / f"data/matcha_flavoured_plus/function/main/smithing_enchantments/{name}.mcfunction"
            apply_path = (
                ROOT / f"data/matcha_flavoured_plus/function/main/smithing_enchantments/apply/{name}.mcfunction"
            )
            player_path = (
                ROOT
                / f"data/matcha_flavoured_plus/function/main/smithing_enchantments/apply_player/{name}.mcfunction"
            )
            with self.subTest(recipe=name):
                if not entry["enchantments"]:
                    for path in (
                        advancement_path,
                        modifier_path,
                        reward_path,
                        apply_path,
                        player_path,
                    ):
                        self.assertFalse(path.exists(), path)
                    continue

                advancement = read_json(advancement_path)
                self.assertEqual(
                    advancement,
                    {
                        "criteria": {
                            "crafted": {
                                "trigger": "minecraft:recipe_crafted",
                                "conditions": {"recipe_id": f"matcha_flavoured_plus:smithing_table/{name}"},
                            }
                        },
                        "rewards": {
                            "function": f"matcha_flavoured_plus:main/smithing_enchantments/{name}"
                        },
                    },
                )

                tag = f"main.smithing_enchantments.{name}"
                self.assertEqual(
                    reward_path.read_text(encoding="utf-8").splitlines(),
                    [
                        f"advancement revoke @s only matcha_flavoured_plus:main/smithing_enchantments/{name}",
                        f"tag @s add {tag}",
                        f"schedule function matcha_flavoured_plus:main/smithing_enchantments/apply/{name} 1t replace",
                    ],
                )
                self.assertEqual(
                    apply_path.read_text(encoding="utf-8").splitlines(),
                    [
                        f"execute as @a[tag={tag}] run function matcha_flavoured_plus:main/smithing_enchantments/apply_player/{name}",
                        f"tag @a[tag={tag}] remove {tag}",
                    ],
                )
                self.assertEqual(
                    player_path.read_text(encoding="utf-8").splitlines(),
                    [
                        f"item modify entity @s {slot} matcha_flavoured_plus:main/smithing_enchantments/{name}"
                        for slot in generator.PLAYER_SLOTS
                    ],
                )

    def test_material_modifiers_are_identity_scoped_and_minimum_only(self):
        for entry in self.entries:
            if not entry["enchantments"]:
                continue
            name = entry["recipe"]
            modifier = read_json(
                ROOT / f"data/matcha_flavoured_plus/item_modifier/main/smithing_enchantments/{name}.json"
            )
            self.assertEqual(len(modifier), len(entry["enchantments"]) + 1)
            by_enchantment = {}
            for top_level in modifier[:-1]:
                item_filter = top_level["item_filter"]
                self.assertEqual(item_filter["items"], entry["result_id"])
                self.assertEqual(
                    item_filter["components"],
                    generator.pending_identity_components(entry),
                )
                self.assertEqual(
                    item_filter["components"]["minecraft:item_name"],
                    generator.pending_item_name(entry),
                )

                # The target enchantment is the first min-level check beneath
                # any conflict-preservation filters.
                node = top_level["modifier"]
                while (
                    node["function"] == "minecraft:filtered"
                    and "modifier" not in node
                    and "on_fail" in node
                ):
                    node = node["on_fail"]
                target = node["item_filter"]["predicates"]["minecraft:enchantments"][0][
                    "enchantments"
                ]
                by_enchantment[target] = top_level

            self.assertEqual(set(by_enchantment), set(entry["enchantments"]))
            for enchantment, target_level in entry["enchantments"].items():
                material_modifier = by_enchantment[enchantment]
                for current_level in range(0, target_level + 3):
                    with self.subTest(
                        recipe=name,
                        enchantment=enchantment,
                        current_level=current_level,
                    ):
                        levels = {
                            enchantment: current_level,
                            "minecraft:mending": 1,
                        }
                        apply_modifier(material_modifier, levels)
                        self.assertEqual(levels[enchantment], max(current_level, target_level))
                        self.assertEqual(levels["minecraft:mending"], 1)

                for conflict in generator.EXCLUSIVE_CONFLICTS.get(enchantment, ()):
                    with self.subTest(
                        recipe=name, enchantment=enchantment, conflict=conflict
                    ):
                        levels = {conflict: 1, "minecraft:unbreaking": 3}
                        apply_modifier(material_modifier, levels)
                        self.assertNotIn(enchantment, levels)
                        self.assertEqual(levels[conflict], 1)
                        self.assertEqual(levels["minecraft:unbreaking"], 3)

            cleanup = modifier[-1]
            self.assertEqual(
                cleanup["item_filter"],
                {
                    "items": entry["result_id"],
                    "components": {
                        "minecraft:item_name": generator.pending_item_name(entry),
                    },
                },
            )
            self.assertEqual(
                cleanup["modifier"],
                {
                    "function": "minecraft:set_components",
                    "components": {
                        "minecraft:item_name": entry["identity_components"][
                            "minecraft:item_name"
                        ],
                    },
                },
            )

    def test_conflict_policy_covers_current_exclusive_sets(self):
        self.assertEqual(
            set(generator.EXCLUSIVE_CONFLICTS["minecraft:smite"]),
            {
                "minecraft:bane_of_arthropods",
                "minecraft:breach",
                "minecraft:density",
                "minecraft:impaling",
                "minecraft:sharpness",
                "matcha_flavoured_plus:main/slaughter",
            },
        )
        self.assertEqual(
            set(generator.EXCLUSIVE_CONFLICTS["minecraft:fortune"]),
            {"minecraft:silk_touch"},
        )
        self.assertEqual(
            set(generator.EXCLUSIVE_CONFLICTS["minecraft:silk_touch"]),
            {"minecraft:fortune"},
        )
        for protection in (
            "minecraft:blast_protection",
            "minecraft:fire_protection",
        ):
            with self.subTest(protection=protection):
                self.assertEqual(
                    set(generator.EXCLUSIVE_CONFLICTS[protection]),
                    {
                        "minecraft:blast_protection",
                        "minecraft:fire_protection",
                        "minecraft:projectile_protection",
                        "minecraft:protection",
                    }
                    - {protection},
                )


if __name__ == "__main__":
    unittest.main()
