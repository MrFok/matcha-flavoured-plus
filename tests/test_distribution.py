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

SMOKE_SPEC = importlib.util.spec_from_file_location(
    "runtime_smoke", ROOT / "tools" / "runtime_smoke.py"
)
runtime_smoke = importlib.util.module_from_spec(SMOKE_SPEC)
assert SMOKE_SPEC.loader is not None
SMOKE_SPEC.loader.exec_module(runtime_smoke)


class DistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.temp.name)
        cls.artifacts = {
            path.name: path for path in builder.build(cls.output, include_mod=True)
        }

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def names(self, artifact):
        with zipfile.ZipFile(artifact) as archive:
            return archive.namelist()

    def artifact(self, variant, kind):
        return self.artifacts[builder.archive_name(f"{variant}-{kind}")]

    def test_death_penalty_initializes_and_targets_the_dead_player(self):
        hpdown = (ROOT / "data/matcha_flavoured_plus/function/main/mechanic/hpdown.mcfunction").read_text(
            encoding="utf-8"
        )
        scoreboard = (ROOT / "data/matcha_flavoured_plus/function/main/setup/scoreboard.mcfunction").read_text(
            encoding="utf-8"
        )
        set_max_hp = (ROOT / "data/matcha_flavoured_plus/function/main/mechanic/set_max_hp.mcfunction").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "execute as @a[scores={Hearts=0}] run scoreboard players set @s Hearts 20",
            scoreboard,
        )
        self.assertIn("function matcha_flavoured_plus:main/mechanic/set_max_hp", scoreboard)
        self.assertIn(
            "execute as @a[scores={deaths=1..,Hearts=12..}] run scoreboard players remove @s Hearts 2",
            hpdown,
        )
        self.assertIn(
            "execute if entity @a[scores={deaths=1..}] run function matcha_flavoured_plus:main/mechanic/set_max_hp",
            hpdown,
        )
        self.assertIn(
            "execute as @a[scores={deaths=1..}] run scoreboard players set @s deaths 0",
            hpdown,
        )
        self.assertIn(
            "execute as @a[scores={Hearts=10}] run attribute @s minecraft:max_health base set 10",
            set_max_hp,
        )

    def test_crystal_heart_is_deliberately_consumed_not_auto_used(self):
        recipe = json.loads(
            (ROOT / "data/matcha_flavoured_plus/recipe/crafting/crystal_heart.json").read_text(encoding="utf-8")
        )
        loot = json.loads(
            (ROOT / "data/minecraft/loot_table/kleis_items/crystal_heart.json").read_text(
                encoding="utf-8"
            )
        )
        advancement = json.loads(
            (ROOT / "data/matcha_flavoured_plus/advancement/main/mechanics/heart_container_obtained.json").read_text(
                encoding="utf-8"
            )
        )
        process = (ROOT / "data/matcha_flavoured_plus/function/main/mechanic/process_heart_container.mcfunction").read_text(
            encoding="utf-8"
        )
        hpdown = (ROOT / "data/matcha_flavoured_plus/function/main/mechanic/hpdown.mcfunction").read_text(
            encoding="utf-8"
        )
        ticking = (ROOT / "data/matcha_flavoured_plus/function/main/setup/ticking_functions.mcfunction").read_text(
            encoding="utf-8"
        )

        self.assertIn("minecraft:consumable", recipe["result"]["components"])
        self.assertTrue(recipe["result"]["components"]["minecraft:food"]["can_always_eat"])
        loot_components = loot["pools"][0]["entries"][0]["functions"][0]["components"]
        self.assertIn("minecraft:consumable", loot_components)
        self.assertTrue(loot_components["minecraft:food"]["can_always_eat"])
        self.assertEqual(
            advancement["criteria"]["consumed_heart_container"]["trigger"],
            "minecraft:consume_item",
        )
        self.assertNotIn("minecraft:inventory_changed", json.dumps(advancement))
        self.assertIn("execute if score @s Hearts matches ..58 run scoreboard players add @s Hearts 2", process)
        self.assertIn("execute if score @s Hearts matches 60.. run loot give @s loot minecraft:kleis_items/crystal_heart", process)
        initializer = "execute unless score @s Hearts matches 10..60 run scoreboard players set @s Hearts 20"
        self.assertIn(initializer, process)
        self.assertIn(
            "execute as @a unless score @s Hearts matches 10..60 run scoreboard players set @s Hearts 20",
            ticking,
        )
        self.assertIn(
            "execute as @a[scores={deaths=1..}] unless score @s Hearts matches 10..60 run scoreboard players set @s Hearts 20",
            hpdown,
        )
        self.assertNotIn("container.*", process)
        self.assertFalse((ROOT / "data/matcha_flavoured_plus/function/main/mechanic/clear_heart_container.mcfunction").exists())

    def test_enchanting_table_uses_silk_touch_and_falls_back_to_obsidian(self):
        loot_table = json.loads(
            (ROOT / "data/minecraft/loot_table/blocks/enchanting_table.json").read_text(
                encoding="utf-8"
            )
        )
        pack_metadata = json.loads((ROOT / "pack.mcmeta").read_text(encoding="utf-8"))
        self.assertIn(
            {"namespace": "minecraft", "path": "recipe/enchanting_table.json"},
            pack_metadata["filter"]["block"],
        )
        self.assertEqual(len(loot_table["pools"]), 3)
        silk_pool, fallback_pool, book_pool = loot_table["pools"]
        self.assertEqual(silk_pool["entries"][0]["name"], "minecraft:enchanting_table")
        self.assertEqual(
            silk_pool["conditions"][1]["predicate"]["predicates"]["minecraft:enchantments"][0],
            {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}},
        )
        self.assertEqual(fallback_pool["entries"][0]["name"], "minecraft:obsidian")
        self.assertEqual(
            fallback_pool["entries"][0]["functions"],
            [{"function": "minecraft:set_count", "count": 4}],
        )
        self.assertEqual(fallback_pool["conditions"][1]["condition"], "minecraft:inverted")
        self.assertEqual(
            book_pool["rolls"],
            {"type": "minecraft:uniform", "min": 2, "max": 5},
        )
        self.assertEqual(book_pool["entries"][0]["name"], "minecraft:book")
        self.assertEqual(
            book_pool["entries"][0]["functions"][0],
            {
                "function": "minecraft:enchant_randomly",
                "options": "#minecraft:in_enchanting_table",
            },
        )
        self.assertEqual(book_pool["conditions"][1]["condition"], "minecraft:inverted")

        mixin = (
            ROOT / "src/main/java/com/mrfok/matcha/mixin/EnchantmentMenuMixin.java"
        ).read_text(encoding="utf-8")
        runtime = (
            ROOT / "src/main/java/com/mrfok/matcha/MatchaFlavouredPlus.java"
        ).read_text(encoding="utf-8")
        table_entity = (
            ROOT / "src/main/java/com/mrfok/matcha/mixin/EnchantingTableBlockEntityMixin.java"
        ).read_text(encoding="utf-8")
        self.assertIn("ENCHANTING_TABLE_LIMIT", runtime)
        self.assertIn("dropExhaustedTableRewards", runtime)
        self.assertIn("new ItemStack(Items.OBSIDIAN, 4)", runtime)
        self.assertIn("2 + level.getRandom().nextInt(4)", runtime)
        self.assertIn("recordEnchant", mixin)
        self.assertIn("player.level().isClientSide()", mixin)
        self.assertIn("enchantSlots.getItem(0)", mixin)
        self.assertIn("Items.BOOK", mixin)
        self.assertIn("DataSlot.standalone()", mixin)
        self.assertNotIn("abstract DataSlot addDataSlot", mixin)
        self.assertIn("AbstractContainerMenuInvoker", mixin)
        self.assertIn("matcha$refreshRemainingUses", mixin)
        self.assertIn("matcha$ignoreExperienceRequirement", mixin)
        self.assertIn("matcha$doNotConsumeExperience", mixin)
        self.assertIn('"matcha_flavoured_plus:enchanting_table_uses"', table_entity)

        book_slot = (
            ROOT / "src/main/java/com/mrfok/matcha/MatchaEnchantmentBookSlot.java"
        ).read_text(encoding="utf-8")
        self.assertIn("extends Slot", book_slot)
        self.assertIn("boolean mayPlace", book_slot)
        self.assertIn("return stack.is(Items.BOOK)", book_slot)
        self.assertIn("int getMaxStackSize()", book_slot)
        self.assertIn("matcha$replaceInputSlot", mixin)
        self.assertIn("ordinal = 0", mixin)

        mixins = json.loads(
            (ROOT / "src/main/resources/matcha_flavoured_plus.mixins.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn("EnchantmentMenuBookSlotMixin", mixins["mixins"])
        self.assertIn("AbstractContainerMenuInvoker", mixins["mixins"])

        menu_invoker = (
            ROOT / "src/main/java/com/mrfok/matcha/mixin/AbstractContainerMenuInvoker.java"
        ).read_text(encoding="utf-8")
        self.assertIn("@Mixin(AbstractContainerMenu.class)", menu_invoker)
        self.assertIn('@Invoker("addDataSlot")', menu_invoker)

        block_item = (
            ROOT / "src/main/java/com/mrfok/matcha/mixin/BlockItemMixin.java"
        ).read_text(encoding="utf-8")
        self.assertIn("shift = At.Shift.BEFORE", block_item)

        hud = (
            ROOT / "src/main/java/com/mrfok/matcha/mixin/client/HudMixin.java"
        ).read_text(encoding="utf-8")
        self.assertIn("matcha$hideFoodBar", hud)
        self.assertIn("matcha$hideExperienceContext", hud)
        self.assertIn("matcha$hideExperienceLevel", hud)
        self.assertIn("matcha$hideFoodBar", hud)
        self.assertIn('method = "extractFood"', hud)
        self.assertIn("matcha$skipExperienceLevel", hud)
        experience_bar = (
            ROOT / "src/main/java/com/mrfok/matcha/mixin/client/ExperienceBarMixin.java"
        ).read_text(encoding="utf-8")
        self.assertIn("matcha$hideExperienceBackground", experience_bar)
        self.assertIn("matcha$hideExperienceProgress", experience_bar)
        enchantment_screen = (
            ROOT / "src/main/java/com/mrfok/matcha/mixin/client/EnchantmentScreenMixin.java"
        ).read_text(encoding="utf-8")
        self.assertIn("matcha$ignoreDisplayedExperienceForChoices", enchantment_screen)
        self.assertIn("matcha$ignoreDisplayedExperienceForTooltip", enchantment_screen)
        self.assertIn("matcha$drawBookBudget", enchantment_screen)
        self.assertIn('Component.literal(remaining + " left")', enchantment_screen)
        self.assertNotIn("@Shadow", enchantment_screen)
        self.assertIn("Minecraft.getInstance().font", enchantment_screen)
        self.assertIn("((MenuAccess<?>) (Object) this).getMenu()", enchantment_screen)
        self.assertIn("graphics.guiWidth()", enchantment_screen)
        self.assertIn("graphics.guiHeight()", enchantment_screen)

        destroy = (
            ROOT / "src/main/java/com/mrfok/matcha/mixin/BlockPlayerDestroyMixin.java"
        ).read_text(encoding="utf-8")
        self.assertIn('method = "playerDestroy"', destroy)
        self.assertIn("preserveCarriedUsesOnDroppedTable", destroy)
        self.assertIn("matcha$captureExistingDrops", destroy)
        self.assertIn("existingEntityIds.contains(itemEntity.getId())", runtime)
        self.assertIn("ThreadLocal<Set<Integer>>", destroy)
        self.assertIn("matcha$existingDrops.remove()", destroy)

    def test_expected_filenames_and_root_layout(self):
        expected = {
            builder.archive_name("resource-pack"),
            *(
                builder.archive_name(f"{variant}-{kind}")
                for variant in builder.PACK_VARIANTS
                for kind in ("datapack", "mod")
            ),
        }
        self.assertEqual(set(self.artifacts), expected)
        allowed_roots = {
            "data",
            "assets",
            "META-INF",
            "com",
            "fabric.mod.json",
            "matcha_flavoured_plus.mixins.json",
            "quilt.mod.json",
            *builder.ROOT_FILES,
        }
        for artifact in self.artifacts.values():
            for name in self.names(artifact):
                self.assertIn(name.split("/", 1)[0], allowed_roots, name)
                self.assertFalse(name.startswith(("matcha_flavoured_plus/", "dist/", ".git/")))

    def test_default_build_is_datapack_and_resource_pack_only(self):
        with tempfile.TemporaryDirectory() as directory:
            artifacts = builder.build(Path(directory))
            names = {artifact.name for artifact in artifacts}
            expected = {
                builder.archive_name("resource-pack"),
                *(
                    builder.archive_name(f"{variant}-datapack")
                    for variant in builder.PACK_VARIANTS
                ),
            }
            self.assertEqual(names, expected)
            self.assertFalse(any(name.endswith("-mod.jar") for name in names))
            for artifact in artifacts:
                with self.subTest(artifact=artifact.name), zipfile.ZipFile(artifact) as archive:
                    names_in_archive = set(archive.namelist())
                    if artifact.name.endswith("-datapack.zip"):
                        self.assertFalse(any(name.startswith("assets/") for name in names_in_archive))
                        self.assertNotIn("fabric.mod.json", names_in_archive)

    def test_content_boundaries(self):
        resource_pack = self.names(
            self.artifacts[builder.archive_name("resource-pack")]
        )
        self.assertTrue(any(name.startswith("assets/") for name in resource_pack))
        self.assertFalse(any(name.startswith("data/") for name in resource_pack))
        all_names = [resource_pack]
        for variant in builder.PACK_VARIANTS:
            datapack = self.names(self.artifact(variant, "datapack"))
            mod = self.names(self.artifact(variant, "mod"))
            self.assertTrue(any(name.startswith("data/") for name in datapack))
            self.assertFalse(any(name.startswith("assets/") for name in datapack))
            self.assertTrue(any(name.startswith("data/") for name in mod))
            self.assertTrue(any(name.startswith("assets/") for name in mod))
            all_names.extend((datapack, mod))
        for names in all_names:
            self.assertTrue(set(builder.ROOT_FILES).issubset(names))
            self.assertFalse(any(name.startswith((".git/", "tools/", "tests/", "dist/")) for name in names))
            self.assertNotIn("respackopts.json5", names)

    def test_default_visual_policy_is_vanilla_first_but_keeps_item_glints(self):
        resource_pack = set(self.names(self.artifacts[builder.archive_name("resource-pack")]))
        self.assertIn("assets/minecraft/items/adamant_mattock.json", resource_pack)
        self.assertIn("assets/minecraft/models/item/adamant_mattock.json", resource_pack)
        self.assertIn("assets/minecraft/textures/item/adamant_mattock.png", resource_pack)
        self.assertIn("assets/minecraft/textures/misc/enchanted_glint_item.png", resource_pack)
        self.assertIn("assets/minecraft/textures/misc/enchanted_glint_armor.png", resource_pack)
        self.assertIn("assets/minecraft/lang/en_us.json", resource_pack)
        custom_block_assets = {
            "assets/minecraft/blockstates/bedrock_buster.json",
            "assets/minecraft/blockstates/warding_stone.json",
            "assets/minecraft/models/block/bedrock_buster.json",
            "assets/minecraft/models/block/warding_stone.json",
            "assets/minecraft/textures/block/bedrock_buster_bottom.png",
            "assets/minecraft/textures/block/bedrock_buster_side.png",
            "assets/minecraft/textures/block/bedrock_buster_top.png",
            "assets/minecraft/textures/block/warding_stone_side.png",
        }
        self.assertEqual(
            {
                name
                for name in resource_pack
                if name.startswith(
                    (
                        "assets/minecraft/blockstates/",
                        "assets/minecraft/models/block/",
                        "assets/minecraft/textures/block/",
                    )
                )
            },
            custom_block_assets,
        )
        hidden_hud = {
            "assets/minecraft/textures/gui/sprites/hud/experience_bar_background.png",
            "assets/minecraft/textures/gui/sprites/hud/experience_bar_progress.png",
            "assets/minecraft/textures/gui/sprites/hud/food_empty.png",
            "assets/minecraft/textures/gui/sprites/hud/food_empty_hunger.png",
            "assets/minecraft/textures/gui/sprites/hud/food_full.png",
            "assets/minecraft/textures/gui/sprites/hud/food_full_hunger.png",
            "assets/minecraft/textures/gui/sprites/hud/food_half.png",
            "assets/minecraft/textures/gui/sprites/hud/food_half_hunger.png",
        }
        self.assertEqual(
            {name for name in resource_pack if name.startswith("assets/minecraft/textures/gui/")},
            hidden_hud,
        )
        self.assertFalse(any(name.startswith("assets/minecraft/textures/entity/") and "/equipment/" not in name for name in resource_pack))

    def test_owned_loot_tables_are_packaged_under_matcha_namespace(self):
        for variant in builder.PACK_VARIANTS:
            for kind in ("datapack", "mod"):
                with self.subTest(variant=variant, kind=kind), zipfile.ZipFile(self.artifact(variant, kind)) as archive:
                    names = set(archive.namelist())
                    self.assertIn("data/matcha_flavoured_plus/loot_table/main/crystal_heart.json", names)
                    self.assertNotIn("data/minecraft/loot_table/kleis_items/crystal_heart.json", names)
                    data_entries = [
                        archive.read(name)
                        for name in names
                        if name.startswith("data/") and not name.endswith("/")
                    ]
                    self.assertFalse(any(b"minecraft:kleis_items" in payload for payload in data_entries))

    def test_bastion_loot_does_not_reference_a_missing_matcha_table(self):
        bastion = json.loads(
            (ROOT / "data/minecraft/loot_table/chests/bastion_other.json").read_text(
                encoding="utf-8"
            )
        )
        payload = json.dumps(bastion)
        self.assertNotIn("matcha_flavoured_plus:main/golden_apple", payload)
        self.assertIn('"value": "minecraft:food/golden_apple"', payload)

    def test_matcha_loot_table_references_resolve_and_use_valid_contexts(self):
        loot_root = ROOT / "data/minecraft/loot_table"
        ruin = json.loads(
            (loot_root / "chests/adventure_old/ruin_generic_storage.json").read_text(
                encoding="utf-8"
            )
        )
        references = {
            entry["value"]
            for pool in ruin["pools"]
            for entry in pool["entries"]
            if entry.get("type") == "minecraft:loot_table"
        }
        expected = {
            "minecraft:chests/adventure_old/ruin_armoury",
            "minecraft:chests/adventure_old/ruin_coal",
            "minecraft:chests/adventure_old/ruin_grains",
            "minecraft:chests/adventure_old/ruin_kitchen",
        }
        self.assertEqual(references, expected)
        for reference in references:
            namespace, path = reference.split(":", 1)
            self.assertEqual(namespace, "minecraft")
            self.assertTrue((loot_root / f"{path}.json").is_file(), reference)

        skeleton = json.loads(
            (loot_root / "entities/skeleton.json").read_text(encoding="utf-8")
        )
        serialized = json.dumps(skeleton)
        self.assertNotIn("minecraft:match_tool", serialized)
        skull_conditions = skeleton["pools"][3]["conditions"]
        axe_condition = next(
            condition
            for condition in skull_conditions
            if condition["condition"] == "minecraft:entity_properties"
        )
        self.assertEqual(axe_condition["entity"], "attacker")
        self.assertEqual(
            axe_condition["predicate"]["equipment"]["mainhand"]["items"],
            "#minecraft:axes",
        )

    def test_loader_metadata_and_json(self):
        for variant in builder.PACK_VARIANTS:
            with self.subTest(variant=variant), zipfile.ZipFile(self.artifact(variant, "mod")) as archive:
                fabric = json.loads(archive.read("fabric.mod.json"))
                quilt = json.loads(archive.read("quilt.mod.json"))
                pack = json.loads(archive.read("pack.mcmeta"))
                forge = archive.read("META-INF/mods.toml").decode()
                neoforge = archive.read("META-INF/neoforge.mods.toml").decode()
            self.assertEqual(pack["pack"]["min_format"], [88, 0])
            self.assertEqual(pack["pack"]["max_format"], [107, 1])
            self.assertEqual(fabric["id"], builder.PROJECT_ID)
            self.assertEqual(fabric["depends"]["minecraft"], "=26.2")
            minecraft_dependency = next(
                dependency
                for dependency in quilt["quilt_loader"]["depends"]
                if dependency["id"] == "minecraft"
            )
            self.assertEqual(minecraft_dependency["versions"], "=26.2")
            self.assertEqual(fabric["description"], "Matcha Flavoured Plus gameplay with vanilla world/UI assets and Matcha item visuals.")
            self.assertEqual(
                fabric["entrypoints"],
                {"main": ["com.mrfok.matcha.MatchaFlavouredPlus"]},
            )
            self.assertEqual(fabric["mixins"], ["matcha_flavoured_plus.mixins.json"])
            self.assertIn("fabric-api", fabric["depends"])
            self.assertIn("fabric-resource-loader-v0", fabric["depends"])
            self.assertNotIn("suggests", fabric)
            self.assertEqual(quilt["quilt_loader"]["id"], builder.PROJECT_ID)
            self.assertEqual(quilt["quilt_loader"]["metadata"]["description"], "Matcha Flavoured Plus gameplay with vanilla world/UI assets and Matcha item visuals.")
            quilt_dependencies = {dependency["id"]: dependency for dependency in quilt["quilt_loader"]["depends"]}
            self.assertEqual(quilt_dependencies["quilt_resource_loader"]["unless"], "fabric-resource-loader-v0")
            self.assertIn('modLoader="lowcodefml"', forge)
            self.assertIn('description="Matcha Flavoured Plus gameplay with vanilla world/UI assets and Matcha item visuals."', forge)
            self.assertIn('loaderVersion="[40,)"', forge)
            self.assertIn("showAsResourcePack=false", forge)
            self.assertIn('modLoader="javafml"', neoforge)
            self.assertIn('loaderVersion="[1,)"', neoforge)
            self.assertIn("showAsResourcePack=false", neoforge)

    def test_mod_build_preflights_runtime_and_does_not_reuse_compiled_classes(self):
        source = (ROOT / "tools/build_distribution.py").read_text(encoding="utf-8")
        self.assertIn("verify_mixin_runtime_contracts(minecraft, javap)", source)
        self.assertIn('"--release",', source)
        self.assertIn('"21",', source)
        self.assertNotIn("if marker.is_file()", source)
        self.assertIn("Never guess between multiple local profiles", source)
        self.assertNotIn("preferred = profiles_root", source)

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

    def test_sweet_berry_behavior_is_item_id_driven(self):
        advancement = json.loads(
            (
                ROOT / "data/matcha_flavoured_plus/advancement/main/mechanics/sweet_berries_eaten.json"
            ).read_text(encoding="utf-8")
        )
        criterion = advancement["criteria"]["eat_sweet_berries"]
        self.assertEqual(criterion["trigger"], "minecraft:consume_item")
        self.assertEqual(
            criterion["conditions"]["item"], {"items": "minecraft:sweet_berries"}
        )
        self.assertEqual(
            advancement["rewards"]["function"],
            "matcha_flavoured_plus:main/effects/sweet_berry_regeneration",
        )

        effect = (
            ROOT / "data/matcha_flavoured_plus/function/main/effects/sweet_berry_regeneration.mcfunction"
        ).read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            effect,
            [
                "effect give @s minecraft:regeneration 1 2 true",
                "advancement revoke @s only matcha_flavoured_plus:main/mechanics/sweet_berries_eaten",
            ],
        )
        scheduled_uses = [
            path
            for path in (ROOT / "data/matcha_flavoured_plus/function/main").rglob("*.mcfunction")
            if path.name != "sweet_berry_regeneration.mcfunction"
            and "sweet_berry_regeneration" in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(scheduled_uses, [])

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

    def test_pack_paths_are_valid_identifiers(self):
        valid_path = re.compile(r"^[a-z0-9._/-]+$")
        invalid = []
        for directory_name in ("data", "assets"):
            directory = builder.ROOT / directory_name
            for path in directory.rglob("*"):
                if path.is_file():
                    relative_path = path.relative_to(directory).as_posix()
                    if not valid_path.fullmatch(relative_path):
                        invalid.append(f"{directory_name}/{relative_path}")
        self.assertEqual(invalid, [])

    def test_legacy_mechanics_qa_functions_are_shipped(self):
        expected = {
            "start.mcfunction",
            "death_setup.mcfunction",
            "custom_music_setup.mcfunction",
            "predicate_setup.mcfunction",
            "anvil_setup.mcfunction",
            "enchanting_setup.mcfunction",
            "endless_repairs_setup.mcfunction",
        }
        function_dir = ROOT / "data/matcha_flavoured_plus/function/main/qa/legacy_notes"
        self.assertEqual({path.name for path in function_dir.iterdir()}, expected)
        for variant in builder.PACK_VARIANTS:
            names = set(self.names(self.artifact(variant, "datapack")))
            for name in expected:
                with self.subTest(variant=variant, name=name):
                    self.assertIn(f"data/matcha_flavoured_plus/function/main/qa/legacy_notes/{name}", names)

    def test_endless_repairs_qa_explains_default_component_serialization(self):
        instructions = (
            ROOT / "data/matcha_flavoured_plus/function/main/qa/legacy_notes/endless_repairs_setup.mcfunction"
        ).read_text(encoding="utf-8")
        self.assertIn("no repair_cost component", instructions)
        self.assertIn("default value of 0", instructions)

    def test_mod_jar_is_self_contained_with_the_authoritative_assets(self):
        original_asset_names = {
            f"assets/{path.relative_to(ROOT / 'assets').as_posix()}"
            for path in (ROOT / "assets").rglob("*")
            if path.is_file()
        }
        filtered_asset_names = set(
            builder.vanilla_first_assets(
                {
                    name: b""
                    for name in original_asset_names
                }
            )
        )

        self.assertTrue(original_asset_names)
        self.assertLess(len(filtered_asset_names), len(original_asset_names))
        for variant in builder.PACK_VARIANTS:
            with self.subTest(variant=variant), zipfile.ZipFile(self.artifact(variant, "mod")) as archive:
                self.assertTrue(filtered_asset_names.issubset(set(archive.namelist())))

    def test_build_removes_deprecated_resource_pack_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            deprecated = [
                output / builder.archive_name(kind)
                for kind in (
                    "datapack",
                    "mod",
                    "original-resource-pack",
                    "vanilla-resource-pack",
                )
            ]
            deprecated.extend(
                output / builder.archive_name(f"{variant}-{kind}")
                for variant in builder.PACK_VARIANTS
                for kind in ("mod",)
            )
            unrelated = output / "keep-me.zip"
            for artifact in deprecated:
                artifact.write_bytes(b"obsolete")
            unrelated.write_bytes(b"unrelated")

            builder.build(output)

            for artifact in deprecated:
                self.assertFalse(artifact.exists())
            self.assertEqual(unrelated.read_bytes(), b"unrelated")

    def test_advancement_tab_variants_have_their_declared_filter_policy(self):
        with zipfile.ZipFile(self.artifact("clean-tabs", "datapack")) as archive:
            clean_tabs = json.loads(archive.read("pack.mcmeta"))
            clean_tab_names = set(archive.namelist())
        with zipfile.ZipFile(self.artifact("dungeons-and-taverns-compatible", "datapack")) as archive:
            compatible = json.loads(archive.read("pack.mcmeta"))
            compatible_names = set(archive.namelist())
        with zipfile.ZipFile(self.artifact(builder.CANONICAL_VARIANT, "datapack")) as archive:
            canonical = json.loads(archive.read("pack.mcmeta"))
            canonical_names = set(archive.namelist())

        def filtered_roots(metadata):
            return {
                entry["path"]
                for entry in metadata["filter"]["block"]
                if entry.get("namespace") == "minecraft" and entry["path"].startswith("advancement/")
            }

        self.assertEqual(
            filtered_roots(clean_tabs),
            {
                "advancement/adventure",
                "advancement/end",
                "advancement/husbandry",
                "advancement/nether",
                "advancement/story",
            },
        )
        self.assertEqual(
            filtered_roots(compatible),
            set(),
        )
        self.assertEqual(
            filtered_roots(canonical),
            set(builder.VANILLA_ADVANCEMENT_ROOTS),
        )
        self.assertFalse(
            any(name.startswith(builder.DNT_OVERLAY_PREFIX) for name in clean_tab_names)
        )
        self.assertTrue(
            any(name.startswith(builder.DNT_OVERLAY_PREFIX) for name in compatible_names)
        )
        self.assertTrue(
            any(name.startswith(builder.DNT_OVERLAY_PREFIX) for name in canonical_names)
        )

        for kind in ("datapack", "mod"):
            with zipfile.ZipFile(self.artifact("clean-tabs", kind)) as archive:
                self.assertFalse(
                    any(
                        name.startswith(builder.DNT_OVERLAY_PREFIX)
                        for name in archive.namelist()
                    )
                )
            with zipfile.ZipFile(
                self.artifact("dungeons-and-taverns-compatible", kind)
            ) as archive:
                self.assertTrue(
                    any(
                        name.startswith(builder.DNT_OVERLAY_PREFIX)
                        for name in archive.namelist()
                    )
                )
            with zipfile.ZipFile(self.artifact(builder.CANONICAL_VARIANT, kind)) as archive:
                self.assertTrue(
                    any(
                        name.startswith(builder.DNT_OVERLAY_PREFIX)
                        for name in archive.namelist()
                    )
                )
                metadata = json.loads(archive.read("pack.mcmeta"))
                self.assertEqual(filtered_roots(metadata), set(builder.VANILLA_ADVANCEMENT_ROOTS))

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
        advancement_path = ROOT / "data/matcha_flavoured_plus/advancement/main/tutorial/catch_everything.json"
        advancement = json.loads(advancement_path.read_text(encoding="utf-8"))
        self.assertIn("alaska_blackfish", advancement["criteria"])
        self.assertNotIn("alaksa_blackfish", advancement["criteria"])
        self.assertIn(["alaska_blackfish"], advancement["requirements"])
        self.assertNotIn(["alaksa_blackfish"], advancement["requirements"])
        self.assertEqual(
            advancement["criteria"]["alaska_blackfish"]["conditions"]["item"]["components"]
            ["minecraft:item_model"],
            "minecraft:alaska_blackfish",
        )

    def test_divine_upgrade_content_is_marked_and_progression_gated(self):
        recipe = json.loads(
            (ROOT / "data/matcha_flavoured_plus/recipe/crafting/fragment_of_tyraels_wings.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(recipe["type"], "minecraft:crafting_shaped")
        self.assertEqual(
            recipe["pattern"],
            ["FDF", "DDD", "FDF"],
        )
        self.assertEqual(
            recipe["key"],
            {"D": "minecraft:diamond", "F": "minecraft:nether_star"},
        )
        self.assertEqual(recipe["result"]["id"], "minecraft:feather")
        fragment_components = recipe["result"]["components"]
        self.assertEqual(
            fragment_components["minecraft:custom_data"],
            {"matcha": {"divine_fragment": True}},
        )
        self.assertEqual(
            fragment_components["minecraft:item_model"],
            "minecraft:fragment_of_tyraels_wings",
        )
        self.assertTrue(fragment_components["minecraft:enchantment_glint_override"])
        unlock = json.loads(
            (
                ROOT
                / "data/matcha_flavoured_plus/advancement/main/recipe_unlocks/fragment_of_tyraels_wings.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            unlock["requirements"],
            [["has_diamonds", "has_nether_stars"]],
        )
        self.assertEqual(
            unlock["rewards"]["recipes"],
            ["matcha_flavoured_plus:crafting/fragment_of_tyraels_wings"],
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
                    (ROOT / f"data/matcha_flavoured_plus/recipe/smithing_table/{recipe_name}.json").read_text(encoding="utf-8")
                )
                self.assertEqual(recipe["template"], "minecraft:netherite_upgrade_smithing_template")
                self.assertEqual(recipe["base"]["fabric:type"], "fabric:components")
                self.assertEqual(recipe["base"]["base"], item_id)
                self.assertEqual(
                    recipe["base"]["components"]["minecraft:custom_data"],
                    {"matcha": {"tier": "adamant", "tool": tool}},
                )
                self.assertFalse(recipe["base"]["strict"])
                self.assertEqual(recipe["addition"]["fabric:type"], "fabric:components")
                self.assertEqual(recipe["addition"]["base"], "minecraft:feather")
                self.assertFalse(recipe["addition"]["strict"])
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

    def test_divine_elytra_is_not_shipped(self):
        forbidden_paths = (
            "data/matcha_flavoured_plus/recipe/smithing_table/tyraels_elytra.json",
            "data/matcha_flavoured_plus/advancement/main/end/obtain_tyraels_elytra.json",
            "data/matcha_flavoured_plus/function/main/qa/divine_elytra/setup.mcfunction",
            "data/matcha_flavoured_plus/function/main/tyrael_elytra/boost.mcfunction",
            "data/matcha_flavoured_plus/function/main/tyrael_elytra/trail.mcfunction",
            "data/matcha_flavoured_plus/predicate/main/tyrael_elytra/not_sneaking.json",
            "assets/minecraft/equipment/tyraels_elytra.json",
            "assets/minecraft/items/tyraels_elytra.json",
            "assets/minecraft/models/item/tyraels_elytra.json",
            "assets/minecraft/models/item/tyraels_elytra_broken.json",
            "assets/minecraft/textures/entity/equipment/wings/tyraels_elytra.png",
            "assets/minecraft/textures/item/tyraels_elytra.png",
            "assets/minecraft/textures/item/tyraels_elytra_broken.png",
        )
        for path in forbidden_paths:
            with self.subTest(path=path):
                self.assertFalse((ROOT / path).exists())

        for artifact in self.artifacts.values():
            names = set(self.names(artifact))
            with self.subTest(artifact=artifact.name):
                self.assertTrue(names.isdisjoint(forbidden_paths))

        ticking = (ROOT / "data/matcha_flavoured_plus/function/main/setup/ticking_functions.mcfunction").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("tyrael_elytra", ticking)
        self.assertNotIn("Divine Elytra", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertNotIn(
            "modrinth.com/datapack/elytra-boost",
            (ROOT / "CREDITS.txt").read_text(encoding="utf-8"),
        )

    def test_divine_test_kit_is_shipped_with_the_datapack(self):
        test_kit = (
            ROOT / "data/matcha_flavoured_plus/function/main/divine/give_test_kit.mcfunction"
        ).read_text(encoding="utf-8")
        self.assertIn("minecraft:fragment_of_tyraels_wings", test_kit)
        self.assertIn("function matcha_flavoured_plus:main/divine/give_pickaxe_test_set", test_kit)
        self.assertIn("function matcha_flavoured_plus:main/divine/give_dolabra_test_set", test_kit)
        wing_line = next(
            line
            for line in test_kit.splitlines()
            if "minecraft:fragment_of_tyraels_wings" in line
        )
        self.assertIn("minecraft:enchantment_glint_override=true", wing_line)
        self.assertNotIn("minecraft:lore", wing_line)

        for tool, item_model in (
            ("pickaxe", "minecraft:divine_pickaxe"),
            ("dolabra", "minecraft:divine_dolabra"),
        ):
            with self.subTest(tool=tool):
                test_set = (
                    ROOT / f"data/matcha_flavoured_plus/function/main/divine/give_{tool}_test_set.mcfunction"
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
            ROOT / "data/matcha_flavoured_plus/function/main/divine/place_mining_test_wall.mcfunction"
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
        for variant in builder.PACK_VARIANTS:
            with self.subTest(variant=variant):
                names = set(self.names(self.artifact(variant, "mod")))
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
        mechanic_dir = ROOT / "data" / "matcha_flavoured_plus" / "function" / "main" / "mechanic"
        warding_stone = (mechanic_dir / "warding_stone.mcfunction").read_text(encoding="utf-8")
        check_forbidden = (mechanic_dir / "warding_stone_check_forbidden.mcfunction").read_text(encoding="utf-8")
        forbidden = (mechanic_dir / "warding_stone_forbidden.mcfunction").read_text(encoding="utf-8")
        particles = (mechanic_dir / "warding_stone_particles.mcfunction").read_text(encoding="utf-8")
        killer = (mechanic_dir / "warding_stone_killer.mcfunction").read_text(encoding="utf-8")
        advancement = json.loads(
            (ROOT / "data" / "matcha_flavoured_plus" / "advancement" / "main" / "mechanics" / "enter_trial_chamber.json").read_text(
                encoding="utf-8"
            )
        )

        setup_selector = "execute as @e[type=minecraft:armor_stand,tag=WardingStone,tag=!WardingStoneSetup] at @s"
        self.assertEqual(warding_stone.count(setup_selector), 1)
        self.assertIn(
            f"{setup_selector} run function matcha_flavoured_plus:main/mechanic/warding_stone_check_forbidden",
            warding_stone,
        )
        self.assertEqual(
            check_forbidden.splitlines()[0],
            "execute if predicate matcha_flavoured_plus:main/in_trial_chamber run return run function matcha_flavoured_plus:main/mechanic/warding_stone_forbidden",
        )
        self.assertIn("function matcha_flavoured_plus:main/mechanic/warding_stone_particles", check_forbidden)
        self.assertNotIn("@e", forbidden)
        self.assertNotIn("@a", forbidden)
        self.assertNotIn("advancement revoke", forbidden)
        self.assertIn("function matcha_flavoured_plus:main/mechanic/warding_stone_killer", forbidden)
        self.assertIn("tag @s add WardingStoneSetup", particles)
        self.assertIn("kill @s", killer)
        self.assertNotIn("@n[tag=WardingStoneSetup]", killer)
        self.assertNotIn("rewards", advancement)

    def test_rebuild_is_byte_deterministic(self):
        first = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in self.artifacts.items()}
        second_dir = self.output / "again"
        second = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in builder.build(second_dir, include_mod=True)
        }
        self.assertEqual(first, second)

    def test_client_log_smoke_check_rejects_matcha_runtime_failures(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "latest.log"
            log.write_text(
                "[Render thread/INFO]: Minecraft client ready\n",
                encoding="utf-8",
            )
            runtime_smoke.assert_clean_matcha_log(log)

            log.write_text(
                "[Render thread/ERROR]: MixinApplyError in matcha_flavoured_plus\n",
                encoding="utf-8",
            )
            with self.assertRaises(runtime_smoke.RconError):
                runtime_smoke.assert_clean_matcha_log(log)

    def test_runtime_smoke_supports_client_log_only_mode(self):
        smoke_source = (ROOT / "tools" / "runtime_smoke.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"--log-only"', smoke_source)
        self.assertIn(
            'parser.error("--password is required unless --log-only is used")',
            smoke_source,
        )

    def test_client_log_smoke_check_can_require_expected_gpu(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log = Path(temp_dir) / "latest.log"
            log.write_text(
                "[Render thread/INFO]: Using graphics device: "
                "NVIDIA GeForce RTX 5080/PCIe/SSE2 (NVIDIA Corporation)\n",
                encoding="utf-8",
            )
            runtime_smoke.assert_expected_gpu(log, "NVIDIA GeForce RTX 5080")

            with self.assertRaises(runtime_smoke.RconError):
                runtime_smoke.assert_expected_gpu(log, "AMD Radeon")

            log.write_text(
                "[Render thread/INFO]: Minecraft client ready\n",
                encoding="utf-8",
            )
            with self.assertRaises(runtime_smoke.RconError):
                runtime_smoke.assert_expected_gpu(log, "NVIDIA GeForce RTX 5080")


if __name__ == "__main__":
    unittest.main()
