import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "patch_profile_configs", ROOT / "tools" / "patch_profile_configs.py"
)
PATCHER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PATCHER)


WAYSTONES = '''[rules]
enableXpCosts = true
warpRequirements = [
    "$uses_xp -> $xp_points_cost = $distance * $xp_per_block",
]
warpSettings = [
    "$xp_per_block = 0.01",
]
'''
CHUNKLOADERS = '''[Limitations]
    maxLoadedChunksPerPlayer = -1
    inactivityTimeout = 30
'''


class ProfileConfigPatchTests(unittest.TestCase):
    def test_waystones_patch_replaces_xp_with_one_obol(self):
        patched = PATCHER.patch_waystones(WAYSTONES)
        self.assertTrue(PATCHER.waystones_policy_is_applied(patched))
        self.assertIn("item_cost('minecraft:emerald', 1)", patched)
        self.assertNotIn("$xp_points_cost", PATCHER._array_text(patched, "warpRequirements"))

    def test_chunkloader_patch_pins_seven_day_timeout(self):
        patched = PATCHER.patch_chunkloaders(CHUNKLOADERS)
        self.assertTrue(PATCHER.chunkloader_policy_is_applied(patched))
        self.assertIn("inactivityTimeout = 10080", patched)

    def test_apply_is_idempotent_and_keeps_hash_backups(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            config = profile / "config"
            config.mkdir()
            (config / "waystones-common.toml").write_text(WAYSTONES, encoding="utf-8")
            (config / "chunkloaders-common.toml").write_text(CHUNKLOADERS, encoding="utf-8")
            with mock.patch.object(PATCHER, "minecraft_is_running", return_value=False):
                first = PATCHER.apply(profile)
                second = PATCHER.apply(profile)
            self.assertEqual(first, ["patch waystones-common.toml", "patch chunkloaders-common.toml"])
            self.assertEqual(second, [])
            backups = list((profile / "matcha-backups" / "config").iterdir())
            self.assertEqual(len(backups), 2)

    def test_already_compliant_chunkloader_config_is_unchanged(self):
        compliant = CHUNKLOADERS.replace("inactivityTimeout = 30", "inactivityTimeout = 10080")
        self.assertEqual(PATCHER.patch_chunkloaders(compliant), compliant)


if __name__ == "__main__":
    unittest.main()
