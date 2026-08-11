import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_manifest", ROOT / "tools" / "validate_manifest.py")
manifest = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(manifest)


class ManifestTests(unittest.TestCase):
    def test_checked_in_manifest_is_valid(self):
        self.assertEqual(manifest.validate(ROOT / "modpack" / "matcha-flavoured-plus.manifest.json"), [])


if __name__ == "__main__":
    unittest.main()
