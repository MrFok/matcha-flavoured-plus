import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WaterBottleStackingTests(unittest.TestCase):
    def test_conversion_is_event_driven(self):
        tick_functions = (
            ROOT / "data/matcha_flavoured_plus/function/main/setup/ticking_functions.mcfunction"
        ).read_text(encoding="utf-8")
        self.assertNotIn("water_bottle_stacking", tick_functions)

        advancement = json.loads(
            (
                ROOT
                / "data/matcha_flavoured_plus/advancement/main/mechanics/stack_water_bottles.json"
            ).read_text(encoding="utf-8")
        )
        criterion = advancement["criteria"]["water_bottle_added"]
        self.assertEqual(criterion["trigger"], "minecraft:inventory_changed")
        item = criterion["conditions"]["items"][0]
        self.assertEqual(item["items"], "minecraft:potion")
        self.assertEqual(
            item["components"]["minecraft:potion_contents"]["potion"],
            "minecraft:water",
        )

    def test_conversion_preserves_the_removed_count(self):
        conversion = (
            ROOT / "data/matcha_flavoured_plus/function/main/mechanic/water_bottle_stacking.mcfunction"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "execute store result score @s waterBottleCount run clear @s",
            conversion,
        )
        self.assertIn(
            "function matcha_flavoured_plus:main/mechanic/water_bottle_stacking/give with storage "
            "matcha_flavoured_plus:main/water_bottle_stack",
            conversion,
        )
        self.assertNotIn("@a", conversion)
        self.assertNotIn("@p", conversion)

        give = (
            ROOT / "data/matcha_flavoured_plus/function/main/mechanic/water_bottle_stacking/give.mcfunction"
        ).read_text(encoding="utf-8")
        self.assertEqual(
            give,
            '$give @s minecraft:potion[potion_contents={potion:"minecraft:water"},'
            'max_stack_size=64] $(count)\n',
        )


if __name__ == "__main__":
    unittest.main()
