import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load_tool(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_tool("build_distribution_for_advancements", "build_distribution.py")
validator = load_tool("validate_advancements", "validate_advancements.py")


class AdvancementGraphTests(unittest.TestCase):
    def test_source_graph_has_exactly_four_visible_roots(self):
        self.assertEqual(validator.validate(ROOT), [])
        definitions = validator._definitions(ROOT)
        visible_roots = {
            identifier
            for identifier, (_, definition) in definitions.items()
            if definition.get("display") and "parent" not in definition
        }
        self.assertEqual(visible_roots, validator.EXPECTED_VISIBLE_ROOTS)

    def test_canonical_variant_hides_vanilla_roots_and_keeps_dnt_overlay(self):
        canonical = builder.PACK_VARIANTS[builder.CANONICAL_VARIANT]
        self.assertTrue(canonical["include_dnt_overlay"])
        self.assertEqual(
            canonical["blocked_advancement_roots"], builder.VANILLA_ADVANCEMENT_ROOTS
        )


if __name__ == "__main__":
    unittest.main()
