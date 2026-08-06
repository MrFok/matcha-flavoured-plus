import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UpstreamFixTests(unittest.TestCase):
    def test_sleep_objective_exists_before_constants_are_written(self):
        lines = (
            ROOT / "data/main/function/setup/scoreboard.mcfunction"
        ).read_text(encoding="utf-8").splitlines()
        objective = lines.index("scoreboard objectives add sleepTimerScore dummy")
        one = lines.index("scoreboard players set 1 sleepTimerScore 1")
        hundred = lines.index("scoreboard players set 100 sleepTimerScore 100")
        self.assertLess(objective, one)
        self.assertLess(objective, hundred)

    def test_heart_container_and_death_updates_are_player_scoped(self):
        scoreboard = (
            ROOT / "data/main/function/setup/scoreboard.mcfunction"
        ).read_text(encoding="utf-8")
        process = (
            ROOT / "data/main/function/mechanic/process_heart_container.mcfunction"
        ).read_text(encoding="utf-8")
        clear = (
            ROOT / "data/main/function/mechanic/clear_heart_container.mcfunction"
        ).read_text(encoding="utf-8")
        hpdown = (
            ROOT / "data/main/function/mechanic/hpdown.mcfunction"
        ).read_text(encoding="utf-8")
        set_max_hp = (
            ROOT / "data/main/function/mechanic/set_max_hp.mcfunction"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "execute as @a[scores={Hearts=0}] run scoreboard players set @s Hearts 20",
            scoreboard,
        )
        self.assertIn("function main:mechanic/set_max_hp", scoreboard)
        self.assertNotIn("@p", process)
        self.assertNotIn("@p", clear)
        self.assertNotIn("@p", hpdown)
        self.assertNotIn("@p", set_max_hp)
        self.assertIn("execute if score @s Hearts matches ..58", process)
        self.assertIn("clear @s", clear)
        self.assertIn("scoreboard players remove @s Hearts 2", hpdown)
        self.assertIn("attribute @s minecraft:max_health", set_max_hp)

        advancement = json.loads(
            (
                ROOT
                / "data/main/advancement/mechanics/heart_container_obtained.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            advancement["criteria"]["obtained_heart_container"]["trigger"],
            "minecraft:inventory_changed",
        )

    def test_sweet_berry_behavior_is_item_id_driven(self):
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
        self.assertEqual(
            advancement["rewards"]["function"],
            "main:effects/sweet_berry_regeneration",
        )

        effect = (
            ROOT / "data/main/function/effects/sweet_berry_regeneration.mcfunction"
        ).read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            effect,
            [
                "effect give @s minecraft:regeneration 1 2 true",
                "advancement revoke @s only main:mechanics/sweet_berries_eaten",
            ],
        )

        berry_lore = [{"text": "❣", "color": "red", "italic": False}]
        for source in (
            "data/minecraft/loot_table/food/sweet_berries.json",
            "data/minecraft/loot_table/harvest/sweet_berry_bush.json",
            "data/minecraft/loot_table/blocks/sweet_berry_bush.json",
        ):
            with self.subTest(source=source):
                loot_table = json.loads((ROOT / source).read_text(encoding="utf-8"))
                serialized = json.dumps(loot_table)
                self.assertNotIn("minecraft:consumable", serialized)
                self.assertIn("minecraft:lore", serialized)

        trade = json.loads(
            (
                ROOT
                / "data/minecraft/villager_trade/farmer/1/exotic_seed_bundle.json"
            ).read_text(encoding="utf-8")
        )
        berry = next(
            item
            for item in trade["gives"]["components"]["minecraft:bundle_contents"]
            if item["id"] == "minecraft:sweet_berries"
        )
        self.assertEqual(berry["components"]["minecraft:lore"], berry_lore)
        self.assertNotIn("minecraft:consumable", berry["components"])

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
        self.assertIn("minecraft:damage_protection", enchantment["effects"])
        immunity = enchantment["effects"]["minecraft:damage_immunity"]
        self.assertEqual(len(immunity), 1)
        tags = immunity[0]["requirements"]["predicate"]["tags"]
        self.assertIn({"expected": True, "id": "main:ender_pearl"}, tags)
        self.assertIn(
            {"expected": False, "id": "minecraft:bypasses_invulnerability"},
            tags,
        )


if __name__ == "__main__":
    unittest.main()
