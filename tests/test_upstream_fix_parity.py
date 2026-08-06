import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UpstreamFixParityTests(unittest.TestCase):
    def test_sleep_initialization_matches_upstream_contract(self):
        lines = (
            ROOT / "data/main/function/setup/scoreboard.mcfunction"
        ).read_text(encoding="utf-8").splitlines()
        objective = lines.index("scoreboard objectives add sleepTimerScore dummy")
        self.assertLess(objective, lines.index("scoreboard players set 1 sleepTimerScore 1"))
        self.assertLess(objective, lines.index("scoreboard players set 100 sleepTimerScore 100"))

    def test_heart_state_is_player_scoped_and_late_join_safe(self):
        process = (
            ROOT / "data/main/function/mechanic/process_heart_container.mcfunction"
        ).read_text(encoding="utf-8")
        hpdown = (
            ROOT / "data/main/function/mechanic/hpdown.mcfunction"
        ).read_text(encoding="utf-8")
        ticking = (
            ROOT / "data/main/function/setup/ticking_functions.mcfunction"
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
                ROOT / "data/main/advancement/mechanics/sweet_berries_eaten.json"
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
                    (ROOT / f"data/smithing_table/recipe/{name}.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    recipe["result"]["components"]["minecraft:custom_data"][
                        "matcha_smithing_pending"
                    ],
                    name,
                )
                modifier = (
                    ROOT / f"data/main/item_modifier/smithing_enchantments/{name}.json"
                ).read_text(encoding="utf-8")
                self.assertIn(f'"matcha_smithing_pending": "{name}"', modifier)

    def test_feather_falling_negates_ender_pearl_damage(self):
        damage_tag = json.loads(
            (ROOT / "data/main/tags/damage_type/ender_pearl.json").read_text(
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
