import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
MATCHA_NAMESPACE = "matcha_flavoured_plus"
NOVA_STRUCTURES_NAMESPACE = "nova_structures"

DNT_OVERLAY_PATHS = {
    "advancement/root.json",
    "advancement/adventure/find_all_illager_structures.json",
    "advancement/adventure/find_desert_ruins.json",
    "advancement/adventure/find_jungle_ruins.json",
    "advancement/adventure/find_shrine.json",
    "advancement/adventure/find_stray_outlook.json",
    "advancement/adventure/find_trident_trial_monument.json",
    "advancement/end/find_end_lighthouse.json",
    "advancement/end/find_end_ship.json",
    "advancement/nether/find_nether_skeleton.json",
    "advancement/nether/find_piglins.json",
    "advancement/nether/give_netherite_piglin_gold_armor.json",
    "advancement/story/bookworm.json",
}


class NamespaceAndAdamantCompatibilityTests(unittest.TestCase):
    def test_owned_data_has_one_private_namespace_and_keeps_compatibility_overrides(self):
        self.assertEqual(
            {path.name for path in DATA.iterdir() if path.is_dir()},
            {MATCHA_NAMESPACE, "minecraft", NOVA_STRUCTURES_NAMESPACE},
        )
        self.assertTrue((DATA / MATCHA_NAMESPACE / "recipe").is_dir())
        self.assertTrue((DATA / MATCHA_NAMESPACE / "function").is_dir())
        self.assertTrue((DATA / "minecraft" / "loot_table").is_dir())

        archive_paths = [
            path.relative_to(ROOT).as_posix()
            for path in (DATA / MATCHA_NAMESPACE).rglob("*")
            if path.is_file()
        ]
        self.assertTrue(archive_paths)
        self.assertTrue(
            all(path.startswith(f"data/{MATCHA_NAMESPACE}/") for path in archive_paths)
        )

    def test_matcha_load_entrypoints_and_adamant_recipe_ids_resolve(self):
        load = json.loads(
            (DATA / "minecraft/tags/function/load.json").read_text(encoding="utf-8")
        )
        tick = json.loads(
            (DATA / "minecraft/tags/function/tick.json").read_text(encoding="utf-8")
        )
        self.assertEqual(load["values"], [f"{MATCHA_NAMESPACE}:main/setup/load"])
        self.assertEqual(tick["values"], [f"{MATCHA_NAMESPACE}:main/setup/tick"])
        self.assertTrue(
            (DATA / MATCHA_NAMESPACE / "function/main/setup/load.mcfunction").is_file()
        )
        self.assertTrue(
            (DATA / MATCHA_NAMESPACE / "function/main/setup/tick.mcfunction").is_file()
        )

        adamant = json.loads(
            (DATA / MATCHA_NAMESPACE / "recipe/crafting/adamant.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(adamant["result"]["id"], "minecraft:netherite_ingot")
        self.assertTrue(
            (
                DATA
                / MATCHA_NAMESPACE
                / "recipe/smithing_table/adamant_pickaxe.json"
            ).is_file()
        )

    def test_vanilla_netherite_recipe_paths_are_filtered(self):
        metadata = json.loads((ROOT / "pack.mcmeta").read_text(encoding="utf-8"))
        filtered = {
            entry["path"]
            for entry in metadata["filter"]["block"]
            if entry.get("namespace") == "minecraft"
        }
        expected = {
            "recipe/netherite_upgrade_smithing_template.json",
            "recipe/netherite_ingot.json",
            "recipe/netherite_sword_smithing.json",
            "recipe/netherite_pickaxe_smithing.json",
            "recipe/netherite_axe_smithing.json",
            "recipe/netherite_shovel_smithing.json",
            "recipe/netherite_hoe_smithing.json",
            "recipe/netherite_spear_smithing.json",
            "recipe/netherite_helmet_smithing.json",
            "recipe/netherite_chestplate_smithing.json",
            "recipe/netherite_leggings_smithing.json",
            "recipe/netherite_boots_smithing.json",
        }
        self.assertTrue(expected.issubset(filtered))
        self.assertFalse(
            any(
                path.relative_to(DATA / "minecraft").as_posix().startswith("recipe/")
                for path in (DATA / "minecraft").rglob("*")
                if path.is_file()
            )
        )

    def test_matcha_private_tags_use_runtime_tag_paths(self):
        expected = {
            "data/matcha_flavoured_plus/tags/entity_type/main/livestock.json",
            "data/matcha_flavoured_plus/tags/entity_type/main/mundane_hostiles.json",
            "data/matcha_flavoured_plus/tags/entity_type/main/villager_friends.json",
            "data/matcha_flavoured_plus/tags/damage_type/main/ender_pearl.json",
        }
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in (DATA / MATCHA_NAMESPACE / "tags").rglob("*.json")
        }
        self.assertEqual(actual, expected)
        self.assertFalse(
            any((DATA / MATCHA_NAMESPACE / "tags/main").rglob("*.json"))
        )

    def test_installed_integration_language_overrides_use_adamant(self):
        files = (
            ROOT / "assets/create/lang/en_us.json",
            ROOT / "assets/dnt/lang/en_us.json",
            ROOT / "assets/detailab/lang/en_us.json",
            ROOT / "assets/travelersbackpack/lang/en_us.json",
        )
        for path in files:
            with self.subTest(path=path):
                values = json.loads(path.read_text(encoding="utf-8")).values()
                self.assertTrue(any("Adamant" in value for value in values if isinstance(value, str)))
                self.assertFalse(
                    any(
                        "netherite" in value.lower()
                        for value in values
                        if isinstance(value, str)
                    )
                )

    def test_dungeons_and_taverns_advancements_use_a_matcha_owned_tab(self):
        matcha_root = json.loads(
            (
                DATA
                / MATCHA_NAMESPACE
                / "advancement/main/adventure/root.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(matcha_root["display"]["title"]["text"], "Dungeons & Taverns")

        dnt_root = json.loads(
            (DATA / NOVA_STRUCTURES_NAMESPACE / "advancement/root.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            dnt_root["parent"],
            f"{MATCHA_NAMESPACE}:main/adventure/root",
        )

        dnt_rooted = DNT_OVERLAY_PATHS - {
            "advancement/root.json",
            "advancement/nether/give_netherite_piglin_gold_armor.json",
        }
        for relative in dnt_rooted:
            path = DATA / NOVA_STRUCTURES_NAMESPACE / relative
            with self.subTest(path=relative):
                definition = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(definition["parent"], f"{NOVA_STRUCTURES_NAMESPACE}:root")

        adamant_dnt = json.loads(
            (
                DATA
                / NOVA_STRUCTURES_NAMESPACE
                / "advancement/nether/give_netherite_piglin_gold_armor.json"
            ).read_text(encoding="utf-8")
        )
        self.assertIn("Adamant", adamant_dnt["display"]["description"]["fallback"])

        metadata = json.loads((ROOT / "pack.mcmeta").read_text(encoding="utf-8"))
        filtered = {
            entry["path"]
            for entry in metadata["filter"]["block"]
            if entry.get("namespace") == NOVA_STRUCTURES_NAMESPACE
        }
        self.assertTrue(DNT_OVERLAY_PATHS <= filtered)

    def test_modded_storage_replaces_matcha_duplicate_recipes(self):
        recipe_dir = DATA / MATCHA_NAMESPACE / "recipe/crafting"
        self.assertFalse((recipe_dir / "bundle.json").exists())
        self.assertFalse((recipe_dir / "sack.json").exists())
        for advancement_name, removed_recipe in (
            ("sturdy_leather", "matcha_flavoured_plus:crafting/sack"),
            ("tattered_leather", "matcha_flavoured_plus:crafting/bundle"),
        ):
            advancement = json.loads(
                (
                    DATA
                    / MATCHA_NAMESPACE
                    / f"advancement/main/recipe_unlocks/{advancement_name}.json"
                ).read_text(encoding="utf-8")
            )
            self.assertNotIn(removed_recipe, advancement["rewards"]["recipes"])

    def test_hybrid_tool_smithing_is_scoped_to_the_hybrid_item_model(self):
        expected = {
            "adamant_mattock": ("minecraft:diamond_hoe", "minecraft:diamond_mattock"),
            "adamant_dolabra": ("minecraft:diamond_axe", "minecraft:diamond_dolabra"),
            "bronze_mattock": ("minecraft:copper_hoe", "minecraft:copper_mattock"),
            "bronze_dolabra": ("minecraft:copper_axe", "minecraft:copper_dolabra"),
            "electrum_mattock": ("minecraft:diamond_hoe", "minecraft:diamond_mattock"),
            "electrum_dolabra": ("minecraft:diamond_axe", "minecraft:diamond_dolabra"),
            "shakudo_mattock": ("minecraft:copper_hoe", "minecraft:copper_mattock"),
            "shakudo_dolabra": ("minecraft:copper_axe", "minecraft:copper_dolabra"),
            "steel_mattock": ("minecraft:iron_hoe", "minecraft:iron_mattock"),
            "steel_dolabra": ("minecraft:iron_axe", "minecraft:iron_dolabra"),
        }
        for recipe_name, (base_id, item_model) in expected.items():
            with self.subTest(recipe=recipe_name):
                recipe = json.loads(
                    (
                        DATA
                        / MATCHA_NAMESPACE
                        / f"recipe/smithing_table/{recipe_name}.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(recipe["base"]["fabric:type"], "fabric:components")
                self.assertEqual(recipe["base"]["base"], base_id)
                self.assertEqual(
                    recipe["base"]["components"]["minecraft:item_model"], item_model
                )
                self.assertFalse(recipe["base"]["strict"])

        for tier in ("copper", "diamond", "iron"):
            for tool in ("mattock", "dolabra"):
                with self.subTest(tier=tier, tool=tool):
                    recipe = json.loads(
                        (
                            DATA
                            / MATCHA_NAMESPACE
                            / f"recipe/crafting/{tier}_{tool}.json"
                        ).read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        recipe["result"]["components"]["minecraft:item_model"],
                        f"minecraft:{tier}_{tool}",
                    )

        for tier, expected_model in (
            ("diamond", "minecraft:diamond"),
            ("iron", "minecraft:iron"),
        ):
            for tool in ("axe", "hoe"):
                with self.subTest(marked_standard_tool=f"{tier}_{tool}"):
                    recipe = json.loads(
                        (
                            DATA
                            / MATCHA_NAMESPACE
                            / f"recipe/crafting/{tier}_{tool}.json"
                        ).read_text(encoding="utf-8")
                    )
                    self.assertEqual(
                        recipe["result"]["components"]["minecraft:item_model"],
                        f"{expected_model}_{tool}",
                    )

        copper_hoe = json.loads(
            (
                DATA
                / MATCHA_NAMESPACE
                / "recipe/crafting/copper_hoe.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            copper_hoe["result"]["components"]["minecraft:item_model"],
            "minecraft:copper_hoe",
        )

        steel_mattock = json.loads(
            (
                DATA
                / MATCHA_NAMESPACE
                / "recipe/smithing_table/steel_mattock.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(steel_mattock["addition"], "minecraft:resin_brick")

        ordinary = {
            "adamant_hoe": "minecraft:diamond_hoe",
            "adamant_axe": "minecraft:diamond_axe",
            "bronze_hoe": "minecraft:copper_hoe",
            "bronze_axe": "minecraft:copper_axe",
            "electrum_hoe": "minecraft:diamond_hoe",
            "electrum_axe": "minecraft:diamond_axe",
            "shakudo_hoe": "minecraft:copper_hoe",
            "shakudo_axe": "minecraft:copper_axe",
            "steel_hoe": "minecraft:iron_hoe",
            "steel_axe": "minecraft:iron_axe",
        }
        for recipe_name, base_id in ordinary.items():
            with self.subTest(ordinary_recipe=recipe_name):
                recipe = json.loads(
                    (
                        DATA
                        / MATCHA_NAMESPACE
                        / f"recipe/smithing_table/{recipe_name}.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(recipe["base"]["fabric:type"], "fabric:components")
                self.assertEqual(recipe["base"]["base"], base_id)
                self.assertEqual(
                    recipe["base"]["components"],
                    {"minecraft:item_model": base_id},
                )
                self.assertNotIn("strict", recipe["base"])

        for recipe_name in ("adamant_axe", "adamant_hoe"):
            with self.subTest(adamant_output=recipe_name):
                recipe = json.loads(
                    (
                        DATA
                        / MATCHA_NAMESPACE
                        / f"recipe/smithing_table/{recipe_name}.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    recipe["result"]["components"]["minecraft:item_model"],
                    f"{MATCHA_NAMESPACE}:{recipe_name}",
                )
                self.assertTrue(
                    (
                        ROOT
                        / "assets"
                        / MATCHA_NAMESPACE
                        / f"items/{recipe_name}.json"
                    ).is_file()
                )

        for path in (DATA / MATCHA_NAMESPACE / "recipe/smithing_table").glob("*.json"):
            recipe = json.loads(path.read_text(encoding="utf-8"))
            for field in ("template", "base", "addition"):
                value = recipe.get(field)
                if isinstance(value, str):
                    with self.subTest(recipe=path.name, field=field):
                        self.assertIn(":", value)


if __name__ == "__main__":
    unittest.main()
