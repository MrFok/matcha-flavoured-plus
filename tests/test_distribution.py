import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_distribution", ROOT / "tools" / "build_distribution.py")
builder = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(builder)


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name)
        cls.artifacts = {path.name: path for path in builder.build(cls.output)}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

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
        allowed_roots = {
            "data",
            "assets",
            "META-INF",
            "fabric.mod.json",
            "quilt.mod.json",
            *builder.ROOT_FILES,
        }
        for artifact in self.artifacts.values():
            for name in self.names(artifact):
                self.assertIn(name.split("/", 1)[0], allowed_roots, name)
                self.assertFalse(name.startswith(("matcha_flavoured_plus/", "dist/", ".git/")))

    def test_content_boundaries(self):
        datapack = self.names(self.artifacts[builder.archive_name("datapack")])
        resource_pack = self.names(
            self.artifacts[builder.archive_name("resource-pack")]
        )
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
            self.assertNotIn("respackopts.json5", names)

    def test_loader_metadata_and_json(self):
        artifact = self.artifacts[builder.archive_name("mod")]
        with zipfile.ZipFile(artifact) as archive:
            fabric = json.loads(archive.read("fabric.mod.json"))
            quilt = json.loads(archive.read("quilt.mod.json"))
            forge = archive.read("META-INF/mods.toml").decode()
            neoforge = archive.read("META-INF/neoforge.mods.toml").decode()
        self.assertEqual(fabric["id"], builder.PROJECT_ID)
        self.assertEqual(
            fabric["description"],
            "Matcha Flavoured Plus gameplay datapack and original visuals.",
        )
        self.assertIn("fabric-resource-loader-v0", fabric["depends"])
        self.assertNotIn("suggests", fabric)
        self.assertEqual(quilt["quilt_loader"]["id"], builder.PROJECT_ID)
        self.assertEqual(
            quilt["quilt_loader"]["metadata"]["description"],
            "Matcha Flavoured Plus gameplay datapack and original visuals.",
        )
        quilt_dependencies = {
            dependency["id"]: dependency for dependency in quilt["quilt_loader"]["depends"]
        }
        self.assertEqual(
            quilt_dependencies["quilt_resource_loader"]["unless"],
            "fabric-resource-loader-v0",
        )
        self.assertIn('modLoader="lowcodefml"', forge)
        self.assertIn('description="Matcha Flavoured Plus gameplay datapack and original visuals."', forge)
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
        directory = builder.ROOT / "assets"
        for path in directory.rglob("*"):
            if path.is_file():
                relative_path = path.relative_to(directory).as_posix()
                if not valid_path.fullmatch(relative_path):
                    invalid.append(relative_path)
        self.assertEqual(invalid, [])

    def test_mod_jar_is_self_contained_with_the_authoritative_assets(self):
        mod_artifact = self.artifacts[builder.archive_name("mod")]
        with zipfile.ZipFile(mod_artifact) as archive:
            mod_names = set(archive.namelist())
        original_asset_names = {
            f"assets/{path.relative_to(ROOT / 'assets').as_posix()}"
            for path in (ROOT / "assets").rglob("*")
            if path.is_file()
        }

        self.assertTrue(original_asset_names)
        self.assertTrue(original_asset_names.issubset(mod_names))

    def test_build_removes_deprecated_resource_pack_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            deprecated = [
                output / builder.archive_name(kind)
                for kind in (
                    "original-resource-pack",
                    "vanilla-resource-pack",
                )
            ]
            unrelated = output / "keep-me.zip"
            for artifact in deprecated:
                artifact.write_bytes(b"obsolete")
            unrelated.write_bytes(b"unrelated")

            builder.build(output)

            for artifact in deprecated:
                self.assertFalse(artifact.exists())
            self.assertEqual(unrelated.read_bytes(), b"unrelated")

    def test_generated_archive_paths_are_relative(self):
        for artifact in self.artifacts.values():
            for name in self.names(artifact):
                self.assertFalse(name.startswith(("/", "\\")), name)
                self.assertNotRegex(name, r"^[A-Za-z]:")

    def test_chicken_noodle_soup_model_resolves(self):
        item_definition = json.loads(
            (builder.ROOT / "assets/minecraft/items/rabbit_stew.json").read_text(encoding="utf-8")
        )
        cases = item_definition["model"]["cases"]
        soup_case = next(case for case in cases if case["when"] == "chicken_noodle_soup")
        model_id = soup_case["model"]["model"]
        namespace, model_path = (
            model_id.split(":", 1) if ":" in model_id else ("minecraft", model_id)
        )
        self.assertTrue(
            (builder.ROOT / "assets" / namespace / "models" / f"{model_path}.json").is_file()
        )

    def test_known_missing_matcha_item_assets_resolve(self):
        expected_textures = {
            "titanium_dolabra": "minecraft:item/titanium_dolabra",
            "titanium_mattock": "minecraft:item/titanium_mattock",
            "squid_ink_pasta": "minecraft:item/ramen",
            "vegetable_noodles": "minecraft:item/ramen",
            "curry_vindaloo": "minecraft:item/curry_vindaloo",
            "apple_pie": "minecraft:unused/apple_pie",
            "golden_pie": "minecraft:unused/apple_pie",
            "tattered_leather": "minecraft:item/leather",
            "titanium_reinforced_bow": "minecraft:item/bow",
            "titanium_reinforced_bow_pulling_0": "minecraft:item/bow_pulling_0",
            "titanium_reinforced_bow_pulling_1": "minecraft:item/bow_pulling_1",
            "titanium_reinforced_bow_pulling_2": "minecraft:item/bow_pulling_2",
            "vermeil_axe": "minecraft:item/netherite_axe",
            "vermeil_pickaxe": "minecraft:item/netherite_pickaxe",
            "raw_ramen": "minecraft:item/uncooked_ramen",
            "buttered_apple": "minecraft:item/baked_apple",
            "raw_green_curry": "minecraft:item/uncooked_green_curry",
            "raw_curry": "minecraft:item/uncooked_curry",
            "raw_paneer_makhani": "minecraft:item/uncooked_paneer_makhani",
            "lyre": "minecraft:item/bow",
        }

        for model_name, expected_texture in expected_textures.items():
            with self.subTest(model=model_name):
                model_path = (
                    ROOT / f"assets/minecraft/models/item/{model_name}.json"
                )
                self.assertTrue(model_path.is_file(), model_path)
                model = json.loads(model_path.read_text(encoding="utf-8"))
                self.assertEqual(model["textures"]["layer0"], expected_texture)
                namespace, texture_path = expected_texture.split(":", 1)
                self.assertTrue(
                    (
                        ROOT
                        / "assets"
                        / namespace
                        / "textures"
                        / f"{texture_path}.png"
                    ).is_file(),
                    expected_texture,
                )

    def test_blind_fish_assets_and_translations_resolve(self):
        expected = {
            "blind_cave_fish": ("minecraft:item/big_placeholder_fish", "Blind Cave Fish"),
            "blind_minnow": ("minecraft:item/small_placeholder_fish", "Blind Minnow"),
        }

        for fish, (texture, translation) in expected.items():
            with self.subTest(fish=fish):
                item = json.loads(
                    (ROOT / f"assets/minecraft/items/{fish}.json").read_text(encoding="utf-8")
                )
                self.assertEqual(item["model"]["model"], f"minecraft:item/{fish}")
                model = json.loads(
                    (ROOT / f"assets/minecraft/models/item/{fish}.json").read_text(encoding="utf-8")
                )
                self.assertEqual(model["textures"]["layer0"], texture)
                namespace, texture_path = texture.split(":", 1)
                self.assertTrue(
                    (ROOT / "assets" / namespace / "textures" / f"{texture_path}.png").is_file()
                )
                for locale in ("en_us", "en_gb", "en_ca", "en_au"):
                    language = json.loads(
                        (ROOT / f"assets/minecraft/lang/{locale}.json").read_text(encoding="utf-8")
                    )
                    self.assertEqual(language[f"item.kleispack.fish.{fish}"], translation)

    def test_alaska_blackfish_advancement_criterion_matches_the_fishing_model(self):
        advancement_path = ROOT / "data/main/advancement/tutorial/catch_everything.json"
        advancement = json.loads(advancement_path.read_text(encoding="utf-8"))
        self.assertIn("alaska_blackfish", advancement["criteria"])
        self.assertNotIn("alaksa_blackfish", advancement["criteria"])
        self.assertEqual(
            advancement["criteria"]["alaska_blackfish"]["conditions"]["item"]["components"]
            ["minecraft:item_model"],
            "minecraft:alaska_blackfish",
        )

    def test_divine_upgrade_content_is_marked_and_restricted(self):
        fragment = json.loads(
            (ROOT / "data/crafting/recipe/fragment_of_tyraels_wings.json").read_text(encoding="utf-8")
        )
        self.assertEqual(fragment["pattern"], ["FDF", "DDD", "FDF"])
        self.assertEqual(
            fragment["key"],
            {"D": "minecraft:diamond", "F": "minecraft:nether_star"},
        )
        self.assertEqual(fragment["result"]["components"]["minecraft:item_model"], "minecraft:fragment_of_tyraels_wings")
        self.assertNotIn(
            "minecraft:enchantment_glint_override",
            fragment["result"]["components"],
        )

        expected = {
            "divine_pickaxe": (
                "minecraft:netherite_pickaxe",
                "pickaxe",
                ["#minecraft:mineable/pickaxe"],
                71,
            ),
            "divine_axe": ("minecraft:netherite_axe", "axe", ["#minecraft:mineable/axe"], 45),
            "divine_dolabra": (
                "minecraft:netherite_axe",
                "dolabra",
                ["#minecraft:mineable/pickaxe", "#minecraft:mineable/axe"],
                71,
            ),
        }
        for recipe_name, (item_id, tool, block_tags, mining_speed) in expected.items():
            with self.subTest(recipe=recipe_name):
                recipe = json.loads(
                    (ROOT / f"data/smithing_table/recipe/{recipe_name}.json").read_text(encoding="utf-8")
                )
                self.assertEqual(recipe["template"], "minecraft:netherite_upgrade_smithing_template")
                self.assertEqual(recipe["base"]["fabric:type"], "fabric:components")
                self.assertEqual(recipe["base"]["base"], item_id)
                if recipe_name in ("divine_pickaxe", "divine_axe"):
                    self.assertEqual(
                        recipe["base"]["components"]["minecraft:item_name"],
                        {
                            "translate": f"item.minecraft.{item_id.removeprefix('minecraft:')}",
                            "color": "gold",
                        },
                    )
                else:
                    self.assertEqual(
                        recipe["base"]["components"]["minecraft:item_model"],
                        "minecraft:adamant_dolabra",
                    )
                self.assertEqual(recipe["addition"]["fabric:type"], "fabric:components")
                self.assertEqual(recipe["addition"]["base"], "minecraft:feather")
                self.assertEqual(
                    recipe["addition"]["components"]["minecraft:custom_data"]["matcha"],
                    {"divine_fragment": True},
                )
                components = recipe["result"]["components"]
                self.assertEqual(components["minecraft:custom_data"]["matcha"]["tier"], "divine")
                self.assertEqual(components["minecraft:custom_data"]["matcha"]["tool"], tool)
                self.assertNotIn("mode", components["minecraft:custom_data"]["matcha"])
                self.assertEqual(
                    [rule["blocks"] for rule in components["minecraft:tool"]["rules"]], block_tags
                )
                self.assertEqual(components["minecraft:tool"]["rules"][0]["speed"], mining_speed)

    def test_divine_test_kit_is_shipped_with_the_datapack(self):
        test_kit = (
            ROOT / "data/main/function/divine/give_test_kit.mcfunction"
        ).read_text(encoding="utf-8")
        self.assertIn("minecraft:fragment_of_tyraels_wings", test_kit)
        self.assertIn("function main:divine/give_pickaxe_test_set", test_kit)
        self.assertIn("function main:divine/give_dolabra_test_set", test_kit)
        wing_line = next(
            line
            for line in test_kit.splitlines()
            if "minecraft:fragment_of_tyraels_wings" in line
        )
        self.assertNotIn("minecraft:enchantment_glint_override", wing_line)

        for tool, item_model in (
            ("pickaxe", "minecraft:divine_pickaxe"),
            ("dolabra", "minecraft:divine_dolabra"),
        ):
            with self.subTest(tool=tool):
                test_set = (
                    ROOT / f"data/main/function/divine/give_{tool}_test_set.mcfunction"
                ).read_text(encoding="utf-8")
                self.assertEqual(test_set.count("give @s "), 5)
                self.assertIn(item_model, test_set)
                self.assertNotIn('mode:"fortune"', test_set)
                for level in range(1, 6):
                    self.assertIn(f'"minecraft:efficiency":{level}', test_set)
                self.assertNotIn('"minecraft:fortune":3', test_set)
                self.assertNotIn('"minecraft:silk_touch":1', test_set)

    def test_divine_mining_test_wall_covers_target_blocks(self):
        wall = (
            ROOT / "data/main/function/divine/place_mining_test_wall.mcfunction"
        ).read_text(encoding="utf-8")
        for block_id in (
            "minecraft:stone",
            "minecraft:deepslate",
            "minecraft:cobbled_deepslate",
            "minecraft:deepslate_coal_ore",
            "minecraft:deepslate_copper_ore",
            "minecraft:deepslate_iron_ore",
            "minecraft:deepslate_gold_ore",
            "minecraft:deepslate_redstone_ore",
            "minecraft:deepslate_lapis_ore",
            "minecraft:deepslate_diamond_ore",
            "minecraft:deepslate_emerald_ore",
        ):
            with self.subTest(block=block_id):
                self.assertIn(block_id, wall)

    def test_divine_visual_assets_are_shipped_in_mod(self):
        expected = {
            "assets/minecraft/items/fragment_of_tyraels_wings.json",
            "assets/minecraft/models/item/fragment_of_tyraels_wings.json",
            "assets/minecraft/models/item/fragment_of_tyraels_wings_in_hand.json",
            "assets/minecraft/textures/item/fragment_of_tyraels_wings.png",
            "assets/minecraft/items/divine_pickaxe.json",
            "assets/minecraft/items/divine_axe.json",
            "assets/minecraft/items/divine_dolabra.json",
            "assets/minecraft/items/divine_pickaxe_fortune.json",
            "assets/minecraft/items/divine_axe_fortune.json",
            "assets/minecraft/items/divine_dolabra_fortune.json",
        }
        names = set(self.names(self.artifacts[builder.archive_name("mod")]))
        self.assertTrue(expected.issubset(names))
        self.assertFalse(any("divine_" in name and "_silk" in name for name in names))
        self.assertNotIn("assets/minecraft/textures/item/fragment_of_tyraels_wings_in_hand.png", names)
        self.assertNotIn("assets/minecraft/models/item/divine_pickaxe_in_hand.json", names)

        held_model = json.loads(
            (ROOT / "assets/minecraft/models/item/fragment_of_tyraels_wings_in_hand.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            held_model["textures"]["layer0"], "minecraft:item/fragment_of_tyraels_wings"
        )
        fragment_texture = (
            ROOT / "assets/minecraft/textures/item/fragment_of_tyraels_wings.png"
        ).read_bytes()
        self.assertEqual(fragment_texture[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", fragment_texture[16:24]), (16, 16))

        pick_texture = (ROOT / "assets/minecraft/textures/item/divine_pickaxe.png").read_bytes()
        self.assertEqual(
            hashlib.sha256(pick_texture).hexdigest(),
            "7e8aab40b66c5d97577fdf184683937dac360584552db2f3fd38926bfb189703",
        )
        pick_icon_model = json.loads(
            (ROOT / "assets/minecraft/models/item/divine_pickaxe.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            pick_icon_model,
            {
                "parent": "minecraft:item/handheld",
                "textures": {"layer0": "minecraft:item/divine_pickaxe"},
            },
        )

        pick_item = json.loads(
            (ROOT / "assets/minecraft/items/divine_pickaxe.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            pick_item,
            {
                "model": {
                    "type": "minecraft:model",
                    "model": "minecraft:item/divine_pickaxe",
                }
            },
        )
        legacy_pick = json.loads(
            (
                ROOT / "assets/minecraft/items/divine_pickaxe_fortune.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            legacy_pick,
            {
                "model": {
                    "type": "minecraft:model",
                    "model": "minecraft:item/divine_pickaxe",
                }
            },
        )

        for tool in ("axe", "dolabra"):
            with self.subTest(legacy_model=tool):
                legacy = json.loads(
                    (
                        ROOT
                        / f"assets/minecraft/items/divine_{tool}_fortune.json"
                    ).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    legacy,
                    {
                        "model": {
                            "type": "minecraft:model",
                            "model": f"minecraft:item/divine_{tool}",
                        }
                    },
                )

    def test_warding_stone_trial_chamber_rejection_is_placement_scoped(self):
        mechanic_dir = ROOT / "data" / "main" / "function" / "mechanic"
        warding_stone = (mechanic_dir / "warding_stone.mcfunction").read_text(encoding="utf-8")
        check_forbidden = (mechanic_dir / "warding_stone_check_forbidden.mcfunction").read_text(encoding="utf-8")
        forbidden = (mechanic_dir / "warding_stone_forbidden.mcfunction").read_text(encoding="utf-8")
        particles = (mechanic_dir / "warding_stone_particles.mcfunction").read_text(encoding="utf-8")
        killer = (mechanic_dir / "warding_stone_killer.mcfunction").read_text(encoding="utf-8")
        advancement = json.loads(
            (ROOT / "data" / "main" / "advancement" / "mechanics" / "enter_trial_chamber.json").read_text(
                encoding="utf-8"
            )
        )

        setup_selector = "execute as @e[type=minecraft:armor_stand,tag=WardingStone,tag=!WardingStoneSetup] at @s"
        self.assertEqual(warding_stone.count(setup_selector), 1)
        self.assertIn(
            f"{setup_selector} run function main:mechanic/warding_stone_check_forbidden",
            warding_stone,
        )
        self.assertEqual(
            check_forbidden.splitlines()[0],
            "execute if predicate main:in_trial_chamber run return run function main:mechanic/warding_stone_forbidden",
        )
        self.assertIn("function main:mechanic/warding_stone_particles", check_forbidden)
        self.assertNotIn("@e", forbidden)
        self.assertNotIn("@a", forbidden)
        self.assertNotIn("advancement revoke", forbidden)
        self.assertIn("function main:mechanic/warding_stone_killer", forbidden)
        self.assertIn("tag @s add WardingStoneSetup", particles)
        self.assertIn("kill @s", killer)
        self.assertNotIn("@n[tag=WardingStoneSetup]", killer)
        self.assertNotIn("rewards", advancement)

    def test_rebuild_is_byte_deterministic(self):
        first = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in self.artifacts.items()}
        second_dir = self.output / "again"
        second = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in builder.build(second_dir)}
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
