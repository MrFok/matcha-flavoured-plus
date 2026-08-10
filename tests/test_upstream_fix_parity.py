import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UpstreamFixParityTests(unittest.TestCase):
    def test_sleep_initialization_matches_upstream_contract(self):
        lines = (
            ROOT / "data/matcha_flavoured_plus/function/main/setup/scoreboard.mcfunction"
        ).read_text(encoding="utf-8").splitlines()
        objective = lines.index("scoreboard objectives add sleepTimerScore dummy")
        self.assertLess(objective, lines.index("scoreboard players set 1 sleepTimerScore 1"))
        self.assertLess(objective, lines.index("scoreboard players set 100 sleepTimerScore 100"))

    def test_sleep_speedup_requires_a_single_all_player_quorum(self):
        sleep = (
            ROOT / "data/matcha_flavoured_plus/function/main/mechanic/sleep.mcfunction"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "execute as @a[gamemode=!spectator] run scoreboard players set @s sleepTimerScore 0",
            sleep,
        )
        self.assertIn(
            "execute as @a[gamemode=!spectator] store result score @s sleepTimerScore run data get entity @s SleepTimer",
            sleep,
        )
        self.assertIn(
            "execute if entity @a[gamemode=!spectator] unless entity @a[gamemode=!spectator,scores={sleepTimerScore=..0}] unless entity @a[gamemode=!spectator,scores={sleepTimerScore=100..}] run time add 120",
            sleep,
        )
        self.assertEqual(sleep.count("time add 120"), 1)
        commands = "\n".join(
            line for line in sleep.splitlines() if not line.startswith("#")
        )
        self.assertNotIn("@p", commands)

    def test_crystal_hearts_are_instant_consumables_from_all_sources(self):
        recipe = json.loads(
            (ROOT / "data/matcha_flavoured_plus/recipe/crafting/crystal_heart.json").read_text(
                encoding="utf-8"
            )
        )
        loot = json.loads(
            (ROOT / "data/minecraft/loot_table/kleis_items/crystal_heart.json").read_text(
                encoding="utf-8"
            )
        )
        sources = [
            recipe["result"]["components"]["minecraft:consumable"],
            loot["pools"][0]["entries"][0]["functions"][0]["components"][
                "minecraft:consumable"
            ],
        ]
        for trade_name in ("divine_comedy", "paradise_lost"):
            trade = json.loads(
                (
                    ROOT
                    / f"data/minecraft/villager_trade/librarian/1/{trade_name}.json"
                ).read_text(encoding="utf-8")
            )
            sources.append(trade["gives"]["components"]["minecraft:consumable"])

        for consumable in sources:
            with self.subTest(consumable=consumable):
                self.assertEqual(consumable["consume_seconds"], 0.0)

    def test_tyraels_wings_recipe_is_gated_by_the_divine_materials(self):
        recipe = json.loads(
            (ROOT / "data/matcha_flavoured_plus/recipe/crafting/fragment_of_tyraels_wings.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(recipe["type"], "minecraft:crafting_shaped")
        self.assertEqual(recipe["pattern"], ["FDF", "DDD", "FDF"])
        self.assertEqual(
            recipe["key"],
            {"D": "minecraft:diamond", "F": "minecraft:nether_star"},
        )
        self.assertEqual(
            recipe["result"]["components"]["minecraft:item_model"],
            "minecraft:fragment_of_tyraels_wings",
        )
        self.assertTrue(
            recipe["result"]["components"]["minecraft:enchantment_glint_override"]
        )
        unlock = json.loads(
            (
                ROOT
                / "data/matcha_flavoured_plus/advancement/main/recipe_unlocks/fragment_of_tyraels_wings.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(unlock["requirements"], [["has_diamonds", "has_nether_stars"]])

    def test_heart_state_is_player_scoped_and_late_join_safe(self):
        process = (
            ROOT / "data/matcha_flavoured_plus/function/main/mechanic/process_heart_container.mcfunction"
        ).read_text(encoding="utf-8")
        hpdown = (
            ROOT / "data/matcha_flavoured_plus/function/main/mechanic/hpdown.mcfunction"
        ).read_text(encoding="utf-8")
        ticking = (
            ROOT / "data/matcha_flavoured_plus/function/main/setup/ticking_functions.mcfunction"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "execute unless score @s Hearts matches 10..60 run scoreboard players set @s Hearts 20",
            process,
        )
        self.assertIn(
            "execute as @a unless score @s Hearts matches 10..60 run scoreboard players set @s Hearts 20",
            ticking,
        )
        self.assertIn("scoreboard players remove @s Hearts 2", hpdown)
        self.assertNotIn("@p", process + hpdown)

    def test_sweet_berry_effect_is_item_id_driven(self):
        advancement = json.loads(
            (
                ROOT / "data/matcha_flavoured_plus/advancement/main/mechanics/sweet_berries_eaten.json"
            ).read_text(encoding="utf-8")
        )
        criterion = advancement["criteria"]["eat_sweet_berries"]
        self.assertEqual(criterion["trigger"], "minecraft:consume_item")
        self.assertEqual(
            criterion["conditions"]["item"],
            {"items": "minecraft:sweet_berries"},
        )

    def test_smithing_repair_is_limited_to_marked_outputs(self):
        manifest = json.loads(
            (ROOT / "tools/smithing_enchantment_manifest.json").read_text(
                encoding="utf-8"
            )
        )
        for entry in manifest["recipes"]:
            if not entry["enchantments"]:
                continue
            name = entry["recipe"]
            with self.subTest(recipe=name):
                recipe = json.loads(
                    (ROOT / f"data/matcha_flavoured_plus/recipe/smithing_table/{name}.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    recipe["result"]["components"]["minecraft:item_name"]["extra"][
                        1
                    ]["insertion"],
                    f"matcha_smithing_pending:{name}",
                )
                self.assertNotIn(
                    "matcha_smithing_pending",
                    recipe["result"]["components"].get("minecraft:custom_data", {}),
                )
                modifier = (
                    ROOT / f"data/matcha_flavoured_plus/item_modifier/main/smithing_enchantments/{name}.json"
                ).read_text(encoding="utf-8")
                self.assertIn(f'"insertion": "matcha_smithing_pending:{name}"', modifier)

    def test_feather_falling_negates_ender_pearl_damage(self):
        damage_tag = json.loads(
            (ROOT / "data/matcha_flavoured_plus/tags/damage_type/main/ender_pearl.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(damage_tag["values"], ["minecraft:ender_pearl"])
        enchantment = json.loads(
            (ROOT / "data/minecraft/enchantment/feather_falling.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("minecraft:damage_immunity", enchantment["effects"])


if __name__ == "__main__":
    unittest.main()
