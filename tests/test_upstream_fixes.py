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


if __name__ == "__main__":
    unittest.main()
