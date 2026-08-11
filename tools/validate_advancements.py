#!/usr/bin/env python3
"""Validate Matcha and Dungeons & Taverns advancement graph invariants."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MATCHA_NAMESPACE = "matcha_flavoured_plus"
DNT_NAMESPACE = "nova_structures"
EXPECTED_VISIBLE_ROOTS = frozenset(
    {
        "matcha_flavoured_plus:main/tutorial/root",
        "matcha_flavoured_plus:main/hell/root",
        "matcha_flavoured_plus:main/end/root",
        "matcha_flavoured_plus:main/adventure/root",
    }
)
# The generated Dungeons & Taverns overlay intentionally keeps one parent
# supplied by the upstream mod.  It is not copied into this repository because
# the overlay must remain small and must not replace the upstream advancement.
EXTERNAL_ADVANCEMENT_IDS = frozenset(
    {
        "nova_structures:nether/find_donjon",
    }
)


def _resource_id(namespace: str, relative: Path) -> str:
    return f"{namespace}:{relative.with_suffix('').as_posix()}"


def _definitions(root: Path) -> dict[str, tuple[Path, dict[str, Any]]]:
    definitions: dict[str, tuple[Path, dict[str, Any]]] = {}
    sources = (
        (MATCHA_NAMESPACE, root / "data" / MATCHA_NAMESPACE / "advancement"),
        (DNT_NAMESPACE, root / "data" / DNT_NAMESPACE / "advancement"),
    )
    for namespace, directory in sources:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.json")):
            relative = path.relative_to(directory)
            identifier = _resource_id(namespace, relative)
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                definitions[identifier] = (path, {"__parse_error__": str(error)})
                continue
            definitions[identifier] = (path, payload)
    return definitions


def _qualified(reference: str, namespace: str) -> str:
    return reference if ":" in reference else f"{namespace}:{reference}"


def _check_reward_reference(
    reference: str,
    namespace: str,
    directory_name: str,
    suffix: str,
    root: Path,
    source: Path,
    failures: list[str],
) -> None:
    qualified = _qualified(reference, namespace)
    reference_namespace, reference_path = qualified.split(":", 1)
    # Vanilla references are resolved by Minecraft itself and are not part of
    # this repository's source graph.
    if reference_namespace == "minecraft":
        return
    candidate = root / "data" / reference_namespace / directory_name / f"{reference_path}{suffix}"
    if not candidate.is_file():
        failures.append(f"{source}: missing reward reference {qualified}")


def validate(root: Path = ROOT) -> list[str]:
    """Return graph invariant failures; an empty list means the graph is valid."""

    failures: list[str] = []
    definitions = _definitions(root)
    if not definitions:
        return ["no Matcha or Dungeons & Taverns advancement definitions found"]

    for identifier, (source, definition) in definitions.items():
        if "__parse_error__" in definition:
            failures.append(f"{source}: invalid JSON: {definition['__parse_error__']}")
            continue

        criteria = definition.get("criteria")
        if not isinstance(criteria, dict) or not criteria:
            failures.append(f"{source}: criteria must be a non-empty object")

        requirements = definition.get("requirements")
        if requirements is not None:
            if not isinstance(requirements, list):
                failures.append(f"{source}: requirements must be an array")
            else:
                for group in requirements:
                    if not isinstance(group, list) or not all(
                        isinstance(name, str) and name in (criteria or {}) for name in group
                    ):
                        failures.append(f"{source}: requirements reference an unknown criterion")

        display = definition.get("display")
        if display is not None:
            if not isinstance(display, dict):
                failures.append(f"{source}: display must be an object")
            else:
                icon = display.get("icon")
                if not isinstance(icon, dict) or not isinstance(icon.get("id"), str):
                    failures.append(f"{source}: display icon must contain an item id")
                for field in ("title", "description"):
                    if not isinstance(display.get(field), (str, dict)):
                        failures.append(f"{source}: display.{field} is missing or invalid")

        parent = definition.get("parent")
        if parent is not None:
            if not isinstance(parent, str):
                failures.append(f"{source}: parent must be a resource id")
            else:
                parent_id = _qualified(parent, identifier.split(":", 1)[0])
                if parent_id in definitions:
                    continue
                if parent_id.startswith("minecraft:") or parent_id in EXTERNAL_ADVANCEMENT_IDS:
                    continue
                failures.append(f"{source}: missing parent {parent_id}")

        rewards = definition.get("rewards", {})
        if isinstance(rewards, dict):
            for reference in rewards.get("recipes", []):
                if isinstance(reference, str):
                    _check_reward_reference(
                        reference, identifier.split(":", 1)[0], "recipe", ".json", root, source, failures
                    )
            for reference in rewards.get("loot", []):
                if isinstance(reference, str):
                    _check_reward_reference(
                        reference,
                        identifier.split(":", 1)[0],
                        "loot_table",
                        ".json",
                        root,
                        source,
                        failures,
                    )
            function_references = rewards.get("function", [])
            if isinstance(function_references, str):
                function_references = [function_references]
            for reference in function_references:
                if isinstance(reference, str):
                    _check_reward_reference(
                        reference,
                        identifier.split(":", 1)[0],
                        "function",
                        ".mcfunction",
                        root,
                        source,
                        failures,
                    )

    visible_roots = frozenset(
        identifier
        for identifier, (_, definition) in definitions.items()
        if definition.get("display") and "parent" not in definition
    )
    if visible_roots != EXPECTED_VISIBLE_ROOTS:
        failures.append(
            "visible advancement roots do not match the four-tab contract: "
            f"expected {sorted(EXPECTED_VISIBLE_ROOTS)}, got {sorted(visible_roots)}"
        )

    # Detect cycles among repository-owned parent links.  Vanilla parents are
    # intentionally outside this graph and do not participate in the check.
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visited:
            return
        if identifier in visiting:
            failures.append(f"advancement parent cycle includes {identifier}")
            return
        visiting.add(identifier)
        definition = definitions[identifier][1]
        parent = definition.get("parent")
        if isinstance(parent, str):
            parent_id = _qualified(parent, identifier.split(":", 1)[0])
            if parent_id in definitions:
                visit(parent_id)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in definitions:
        visit(identifier)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    args = parser.parse_args()
    failures = validate(args.root)
    if failures:
        print("Advancement validation failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print("Advancement graph is valid: exactly four visible roots and no broken owned references.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
