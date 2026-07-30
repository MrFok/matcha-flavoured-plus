import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_distribution", ROOT / "tools" / "build_distribution.py")
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.output = Path(self.temp.name)
        self.artifacts = {path.name: path for path in builder.build(self.output)}

    def tearDown(self):
        self.temp.cleanup()

    def names(self, artifact):
        with zipfile.ZipFile(artifact) as archive:
            return archive.namelist()

    def test_expected_filenames_and_root_layout(self):
        expected = {
            builder.archive_name("datapack"),
            builder.archive_name("resource-pack"),
            builder.archive_name("mod"),
        }
        self.assertEqual(set(self.artifacts), expected)
        allowed_roots = {"data", "assets", "META-INF", "fabric.mod.json", "quilt.mod.json", *builder.ROOT_FILES}
        for artifact in self.artifacts.values():
            for name in self.names(artifact):
                self.assertIn(name.split("/", 1)[0], allowed_roots, name)
                self.assertFalse(name.startswith(("matcha_flavoured_plus/", "dist/", ".git/")))

    def test_content_boundaries(self):
        datapack = self.names(self.artifacts[builder.archive_name("datapack")])
        resource_pack = self.names(self.artifacts[builder.archive_name("resource-pack")])
        mod = self.names(self.artifacts[builder.archive_name("mod")])
        self.assertTrue(any(name.startswith("data/") for name in datapack))
        self.assertFalse(any(name.startswith("assets/") for name in datapack))
        self.assertTrue(any(name.startswith("assets/") for name in resource_pack))
        self.assertFalse(any(name.startswith("data/") for name in resource_pack))
        self.assertTrue(any(name.startswith("data/") for name in mod))
        self.assertTrue(any(name.startswith("assets/") for name in mod))
        for names in (datapack, resource_pack, mod):
            self.assertTrue(set(builder.ROOT_FILES).issubset(names))
            self.assertFalse(any(name.startswith((".git/", "tools/", "tests/", "dist/")) for name in names))

    def test_loader_metadata_and_json(self):
        artifact = self.artifacts[builder.archive_name("mod")]
        with zipfile.ZipFile(artifact) as archive:
            fabric = json.loads(archive.read("fabric.mod.json"))
            quilt = json.loads(archive.read("quilt.mod.json"))
            forge = archive.read("META-INF/mods.toml").decode()
            neoforge = archive.read("META-INF/neoforge.mods.toml").decode()
        self.assertEqual(fabric["id"], builder.PROJECT_ID)
        self.assertIn("fabric-resource-loader-v0", fabric["depends"])
        self.assertEqual(quilt["quilt_loader"]["id"], builder.PROJECT_ID)
        quilt_dependencies = {
            dependency["id"]: dependency for dependency in quilt["quilt_loader"]["depends"]
        }
        self.assertEqual(
            quilt_dependencies["quilt_resource_loader"]["unless"],
            "fabric-resource-loader-v0",
        )
        self.assertIn('modLoader="lowcodefml"', forge)
        self.assertIn('loaderVersion="[40,)"', forge)
        self.assertIn("showAsResourcePack=false", forge)
        self.assertIn('modLoader="javafml"', neoforge)
        self.assertIn('loaderVersion="[1,)"', neoforge)
        self.assertIn("showAsResourcePack=false", neoforge)

    def test_source_json_is_valid(self):
        paths = [builder.ROOT / "pack.mcmeta"]
        for directory in ("data", "assets"):
            paths.extend((builder.ROOT / directory).rglob("*.json"))
        empty_paths = set()
        for path in paths:
            relative_path = path.relative_to(builder.ROOT)
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                empty_paths.add(relative_path)
                continue
            with self.subTest(path=relative_path):
                json.loads(text)
        self.assertEqual(empty_paths, set())

    def test_resource_paths_are_valid_identifiers(self):
        valid_path = re.compile(r"^[a-z0-9._/-]+$")
        invalid = []
        for path in (builder.ROOT / "assets").rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(builder.ROOT).as_posix()
                if not valid_path.fullmatch(relative_path):
                    invalid.append(relative_path)
        self.assertEqual(invalid, [])

    def test_rebuild_is_byte_deterministic(self):
        first = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in self.artifacts.items()}
        second_dir = self.output / "again"
        second = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in builder.build(second_dir)}
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
