import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "patch_profile_resourcepacks", ROOT / "tools" / "patch_profile_resourcepacks.py"
)
PATCHER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(PATCHER)


class ProfileResourcePackPatchTests(unittest.TestCase):
    def make_zip(self, root: Path, name: str, entries: dict[str, bytes | str]) -> Path:
        path = root / name
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for entry, value in entries.items():
                archive.writestr(entry, value)
        return path

    def read_zip(self, path: Path) -> dict[str, bytes]:
        with zipfile.ZipFile(path) as archive:
            return {name: archive.read(name) for name in archive.namelist()}

    def test_outline_patch_keeps_pack_and_repairs_inherited_textures(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = {
                "textures": {
                    "0": "item/firstperson/enchanted_wooden_hoe",
                    "particle": "item/firstperson/enchanted_wooden_hoe",
                }
            }
            axe = {
                "textures": {
                    "0": "minecraft:item/thirdperson/enchanted_iron_axe",
                    "particle": "minecraft:item/copper/enchanted_iron_axe",
                }
            }
            pack = self.make_zip(
                root,
                "Enchantment Outlines.zip",
                {
                    "assets/.DS_Store": b"junk",
                    "__MACOSX/assets/._junk": b"junk",
                    "assets/minecraft/models/item/firstperson/hoe/enchanted_hoe.json": json.dumps(parent),
                    "assets/minecraft/models/item/thirdperson/axe/enchanted_iron_axe.json": json.dumps(axe),
                    "assets/minecraft/items/oxidizing_hoe.json": "{}",
                    "assets/minecraft/models/item/oxidizingcopper/firstperson/hoe/exposed.json": "{}",
                },
            )
            self.assertTrue(PATCHER.rewrite_pack(pack, root / "backups", False))
            entries = self.read_zip(pack)
            self.assertNotIn("assets/.DS_Store", entries)
            self.assertNotIn("__MACOSX/assets/._junk", entries)
            self.assertIn("assets/minecraft/items/oxidizing_hoe.json", entries)
            self.assertIn(
                "assets/minecraft/models/item/oxidizingcopper/firstperson/hoe/exposed.json",
                entries,
            )
            repaired_parent = json.loads(entries[
                "assets/minecraft/models/item/firstperson/hoe/enchanted_hoe.json"
            ])
            self.assertEqual(repaired_parent["textures"]["0"], "minecraft:item/wooden/hoe")
            self.assertEqual(repaired_parent["textures"]["particle"], "#0")
            repaired_axe = json.loads(entries[
                "assets/minecraft/models/item/thirdperson/axe/enchanted_iron_axe.json"
            ])
            self.assertEqual(repaired_axe["textures"]["particle"], "#0")
            self.assertEqual(len(list((root / "backups").iterdir())), 1)

    def test_outline_book_model_gets_a_real_particle_texture(self):
        raw = json.dumps({"textures": {"1": "item/outline/book_outlinee"}}).encode()
        repaired = json.loads(PATCHER.patch_outline_model(
            "assets/minecraft/models/item/firstperson/book/book_outline.json", raw
        ))
        self.assertEqual(repaired["textures"]["particle"], "#1")

    def test_recovered_patch_only_removes_known_broken_options(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            broken = next(iter(PATCHER.RECOVERED_BROKEN_OPTIONS))
            pack = self.make_zip(
                root,
                "Re-covered.zip",
                {broken: "option", "assets/carl/textures/item/kept.png": b"png"},
            )
            PATCHER.rewrite_pack(pack, root / "backups", False)
            entries = self.read_zip(pack)
            self.assertNotIn(broken, entries)
            self.assertIn("assets/carl/textures/item/kept.png", entries)

    def test_metadata_patch_adds_current_mandatory_bounds(self):
        raw = json.dumps(
            {"pack": {"pack_format": 64, "supported_formats": [64, 107]}}
        ).encode()
        payload = json.loads(PATCHER.patch_pack_metadata(raw))
        self.assertEqual(payload["pack"]["min_format"], 64)
        self.assertEqual(payload["pack"]["max_format"], 107)

    def test_metadata_patch_is_byte_stable_once_bounds_exist(self):
        raw = b'{"pack":{"supported_formats":[64,107],"min_format":64,"max_format":107}}'
        self.assertIs(PATCHER.patch_pack_metadata(raw), raw)

    def test_apply_restores_vanilla_perfected_identity_packs_and_load_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            profile = Path(temporary)
            enabled = profile / "resourcepacks"
            disabled = profile / "resourcepacks-disabled-by-matcha"
            enabled.mkdir()
            disabled.mkdir()
            for name in PATCHER.PRESERVED_PACKS:
                self.make_zip(
                    disabled,
                    name,
                    {"pack.mcmeta": '{"pack":{"pack_format":64}}'},
                )
            (profile / "options.txt").write_text(
                'resourcePacks:["vanilla","continuity:glass_pane_culling_fix",'
                '"file/Enchantment Outlines.zip","elytratrails:arrowtrails",'
                '"file/C418.zip"]\n',
                encoding="utf-8",
            )

            with mock.patch.object(
                PATCHER, "minecraft_is_running", return_value=False
            ):
                changes = PATCHER.apply(profile)

            self.assertIn(
                "restore Vanilla Perfected resource-pack selection", changes
            )
            for name in PATCHER.PRESERVED_PACKS:
                self.assertTrue((enabled / name).is_file())
                self.assertFalse((disabled / name).exists())

            selected = json.loads(
                (profile / "options.txt").read_text(encoding="utf-8")
                .splitlines()[0]
                .removeprefix("resourcePacks:")
            )
            self.assertLess(
                selected.index("file/Recolourful Containers 3.1.3 (1.19.4+).zip"),
                selected.index("file/Vanilla Tweaks (VP Default).zip"),
            )
            self.assertLess(
                selected.index("file/Enchantment Outlines.zip"),
                selected.index("file/Dani's Oxidizing Copper Tools.zip"),
            )
            self.assertLess(
                selected.index("file/Vanilla Perfected Panorama.zip"),
                selected.index("elytratrails:arrowtrails"),
            )
            self.assertEqual(
                selected[-1], "file/qrafty's-capitalized-font-3.5.zip"
            )


if __name__ == "__main__":
    unittest.main()
