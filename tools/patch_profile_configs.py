#!/usr/bin/env python3
"""Apply Matcha's server-side integration rules to one explicit profile."""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess


WAYSTONES_RULES = (
    "$uses_obol #= and(any(source(is_waystone), source(is_warp_stone)), not(target(is_fleeting_memorial)))",
    "$uses_obol -> item_cost('minecraft:emerald', 1)",
    "is_warp_stone -> damage_item(80)",
    "is_inventory_button -> cooldown_cost('inventory_button', $inventory_button_cooldown)",
)
CHUNKLOADER_TIMEOUT_MINUTES = 7 * 24 * 60


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def minecraft_is_running() -> bool:
    if os.name != "nt":
        return False
    for image in ("javaw.exe", "java.exe"):
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image}", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
        )
        if image.casefold() in result.stdout.casefold():
            return True
    return False


def _newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _array_bounds(lines: list[str], key: str) -> tuple[int, int]:
    start = next(
        (index for index, line in enumerate(lines) if re.match(rf"^{re.escape(key)}\s*=\s*\[\s*$", line.rstrip("\r\n"))),
        None,
    )
    if start is None:
        raise ValueError(f"{key} array not found")
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].strip() == "]"),
        None,
    )
    if end is None:
        raise ValueError(f"{key} array is not terminated")
    return start, end


def _replace_array(text: str, key: str, values: tuple[str, ...]) -> str:
    newline = _newline(text)
    lines = text.splitlines(keepends=True)
    start, end = _array_bounds(lines, key)
    replacement = [f"{key} = [{newline}"]
    replacement.extend(f'    "{value}",{newline}' for value in values)
    replacement.append(f"]{newline}")
    return "".join((*lines[:start], *replacement, *lines[end + 1 :]))


def patch_waystones(raw: str) -> str:
    updated = _replace_array(raw, "warpRequirements", WAYSTONES_RULES)
    updated, count = re.subn(
        r"(?m)^enableXpCosts[ \t]*=[ \t]*(?:true|false)[ \t]*$",
        "enableXpCosts = false",
        updated,
    )
    if count != 1:
        raise ValueError("expected exactly one Waystones enableXpCosts setting")
    return updated


def patch_chunkloaders(raw: str) -> str:
    updated, count = re.subn(
        r"(?m)^[ \t]*inactivityTimeout[ \t]*=[ \t]*\d+[ \t]*$",
        f"    inactivityTimeout = {CHUNKLOADER_TIMEOUT_MINUTES}",
        raw,
    )
    if count != 1:
        raise ValueError("expected exactly one Chunk Loaders inactivityTimeout setting")
    return updated


def waystones_policy_is_applied(raw: str) -> bool:
    return (
        "enableXpCosts = false" in raw
        and "item_cost('minecraft:emerald', 1)" in _array_text(raw, "warpRequirements")
        and "xp_points_cost" not in _array_text(raw, "warpRequirements")
    )


def _array_text(text: str, key: str) -> str:
    lines = text.splitlines()
    start, end = _array_bounds(lines, key)
    return "\n".join(lines[start + 1 : end])


def chunkloader_policy_is_applied(raw: str) -> bool:
    return f"inactivityTimeout = {CHUNKLOADER_TIMEOUT_MINUTES}" in raw


def _backup(path: Path, backup_root: Path) -> Path:
    backup_root.mkdir(parents=True, exist_ok=True)
    destination = backup_root / f"{sha256(path)[:16]}-{path.name}"
    if not destination.exists():
        shutil.copy2(path, destination)
    return destination


def _apply_file(
    path: Path,
    transform,
    policy,
    backup_root: Path,
    dry_run: bool,
) -> str | None:
    raw = path.read_text(encoding="utf-8")
    updated = transform(raw)
    if updated == raw:
        return None
    if dry_run:
        return f"patch {path.name}"
    _backup(path, backup_root)
    path.write_text(updated, encoding="utf-8", newline="")
    if not policy(path.read_text(encoding="utf-8")):
        raise RuntimeError(f"post-write policy check failed for {path}")
    return f"patch {path.name}"


def apply(profile: Path, dry_run: bool = False) -> list[str]:
    config = profile / "config"
    waystones = config / "waystones-common.toml"
    chunkloaders = config / "chunkloaders-common.toml"
    for path in (waystones, chunkloaders):
        if not path.is_file():
            raise FileNotFoundError(f"Required config file not found: {path}")
    if not dry_run and minecraft_is_running():
        raise RuntimeError("Refusing to patch profile configs while Java/Minecraft is running")

    backup_root = profile / "matcha-backups" / "config"
    changes: list[str] = []
    waystone_change = _apply_file(
        waystones, patch_waystones, waystones_policy_is_applied, backup_root, dry_run
    )
    if waystone_change:
        changes.append(waystone_change)
    chunkloader_change = _apply_file(
        chunkloaders,
        patch_chunkloaders,
        chunkloader_policy_is_applied,
        backup_root,
        dry_run,
    )
    if chunkloader_change:
        changes.append(chunkloader_change)
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        type=Path,
        default=Path(os.environ["MATCHA_PROFILE"]) if os.environ.get("MATCHA_PROFILE") else None,
        help="explicit Modrinth profile; defaults to MATCHA_PROFILE",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.profile is None:
        parser.error("provide --profile or set MATCHA_PROFILE; profile auto-discovery is disabled")
    changes = apply(args.profile, args.dry_run)
    for change in changes:
        print(change)
    print(f"{len(changes)} change(s) {'required' if args.dry_run else 'applied'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
