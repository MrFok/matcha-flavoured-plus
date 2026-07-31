import json
from pathlib import Path
import struct
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
HUD = ROOT / "assets" / "minecraft" / "textures" / "gui" / "sprites" / "hud"


def read_rgba_png(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")

    offset = 8
    compressed = bytearray()
    width = height = None
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        offset += length + 12
        if kind == b"IHDR":
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if (bit_depth, color_type, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError(f"{path} is not a non-interlaced 8-bit RGBA PNG")
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break

    if width is None or height is None:
        raise ValueError(f"{path} has no IHDR chunk")

    raw = zlib.decompress(compressed)
    stride = width * 4
    rows = []
    previous = bytearray(stride)
    cursor = 0
    for _ in range(height):
        filter_type = raw[cursor]
        source = raw[cursor + 1 : cursor + 1 + stride]
        cursor += stride + 1
        row = bytearray(stride)
        for index, value in enumerate(source):
            left = row[index - 4] if index >= 4 else 0
            above = previous[index]
            upper_left = previous[index - 4] if index >= 4 else 0
            if filter_type == 0:
                predictor = 0
            elif filter_type == 1:
                predictor = left
            elif filter_type == 2:
                predictor = above
            elif filter_type == 3:
                predictor = (left + above) // 2
            elif filter_type == 4:
                estimate = left + above - upper_left
                distance_left = abs(estimate - left)
                distance_above = abs(estimate - above)
                distance_upper_left = abs(estimate - upper_left)
                predictor = (
                    left
                    if distance_left <= distance_above and distance_left <= distance_upper_left
                    else above
                    if distance_above <= distance_upper_left
                    else upper_left
                )
            else:
                raise ValueError(f"{path} uses unknown PNG filter {filter_type}")
            row[index] = (value + predictor) & 0xFF
        rows.append(row)
        previous = row
    return width, height, rows


class HudCompatibilityTests(unittest.TestCase):
    def test_experience_bar_sprites_are_transparent_and_dimensionally_valid(self):
        for name in ("experience_bar_background.png", "experience_bar_progress.png"):
            with self.subTest(name=name):
                width, height, rows = read_rgba_png(HUD / name)
                self.assertEqual((width, height), (182, 5))
                self.assertTrue(all(channel == 0 for row in rows for channel in row[3::4]))

    def test_vanilla_progression_trees_remain_filtered(self):
        metadata = json.loads((ROOT / "pack.mcmeta").read_text(encoding="utf-8"))
        blocked_paths = {
            item["path"]
            for item in metadata.get("filter", {}).get("block", [])
            if item.get("namespace") == "minecraft"
        }
        required_trees = {
            "advancement/adventure",
            "advancement/end",
            "advancement/nether",
            "advancement/story",
        }
        self.assertTrue(required_trees <= blocked_paths)


if __name__ == "__main__":
    unittest.main()
