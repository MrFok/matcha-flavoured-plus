#!/usr/bin/env python3
"""Build the loader-free combined datapack/resource-pack archive."""

from __future__ import annotations

import argparse
from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ARCHIVE_NAME = "matcha-flavoured-1.03-upstream-fixes-combined.zip"
ROOT_FILES = ("pack.mcmeta", "pack.png", "CREDITS.txt")
EPOCH = (1980, 1, 1, 0, 0, 0)


def source_entries() -> dict[str, bytes]:
    entries = {name: (ROOT / name).read_bytes() for name in ROOT_FILES}
    for directory in ("data", "assets"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file():
                entries[path.relative_to(ROOT).as_posix()] = path.read_bytes()
    return entries


def build(output_dir: Path = DIST) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / ARCHIVE_NAME
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for name, contents in sorted(source_entries().items()):
            info = zipfile.ZipInfo(name, EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, contents, compresslevel=9)
    with zipfile.ZipFile(destination) as archive:
        corrupt_entry = archive.testzip()
    if corrupt_entry is not None:
        raise RuntimeError(f"archive validation failed at {corrupt_entry}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DIST)
    args = parser.parse_args()
    print(build(args.output))


if __name__ == "__main__":
    main()
