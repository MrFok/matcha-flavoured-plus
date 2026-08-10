import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "build_distribution_runtime_paths", ROOT / "tools" / "build_distribution.py"
)
BUILDER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(BUILDER)


class BuildRuntimePathTests(unittest.TestCase):
    def test_explicit_compile_classpath_does_not_require_modrinth(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            minecraft = root / "client.jar"
            loader = root / "fabric-loader.jar"
            mixin = root / "sponge-mixin.jar"
            for path in (minecraft, loader, mixin):
                path.touch()

            environment = {
                "MATCHA_MINECRAFT_JAR": str(minecraft),
                "MATCHA_COMPILE_CLASSPATH": os.pathsep.join((str(loader), str(mixin))),
            }
            with mock.patch.dict(os.environ, environment, clear=True):
                self.assertEqual(
                    BUILDER._runtime_paths(),
                    (minecraft, [loader, mixin]),
                )

    def test_explicit_compile_classpath_fails_closed_on_missing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            minecraft = root / "client.jar"
            minecraft.touch()
            environment = {
                "MATCHA_MINECRAFT_JAR": str(minecraft),
                "MATCHA_COMPILE_CLASSPATH": str(root / "missing.jar"),
            }
            with mock.patch.dict(os.environ, environment, clear=True):
                self.assertIsNone(BUILDER._runtime_paths())


if __name__ == "__main__":
    unittest.main()
