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


if __name__ == "__main__":
    unittest.main()
