"""Generate transparent vanilla-compatible food and XP HUD sprites."""

from __future__ import annotations

from pathlib import Path
import struct
import zlib


ROOT = Path(__file__).resolve().parents[1]
HUD = ROOT / "assets" / "minecraft" / "textures" / "gui" / "sprites" / "hud"
TARGETS = (
    "experience_bar_background.png",
    "experience_bar_progress.png",
    "food_empty.png",
    "food_empty_hunger.png",
    "food_full.png",
    "food_full_hunger.png",
    "food_half.png",
    "food_half_hunger.png",
)


def dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG with an IHDR chunk")
    return struct.unpack(">II", data[16:24])


def chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    )


def transparent_png(width: int, height: int) -> bytes:
    raw = b"".join(b"\x00" + b"\x00" * (width * 4) for _ in range(height))
    return b"\x89PNG\r\n\x1a\n" + chunk(
        b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    ) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def main() -> None:
    for name in TARGETS:
        path = HUD / name
        width, height = dimensions(path)
        path.write_bytes(transparent_png(width, height))
        print(f"{path}: {width}x{height}")


if __name__ == "__main__":
    main()
