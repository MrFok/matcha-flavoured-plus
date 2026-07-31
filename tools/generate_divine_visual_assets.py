#!/usr/bin/env python3
"""Generate the hand-authored Divine item PNG textures from compact pixel rules."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / "assets" / "minecraft" / "textures" / "item"
WING_REFERENCE = ROOT / "tools" / "assets" / "holy_feather_reference.png"

TRANSPARENT = (0, 0, 0, 0)
CHARCOAL = (17, 17, 21, 255)
DARK_METAL = (45, 43, 50, 255)
MID_METAL = (68, 66, 74, 255)
SILVER = (126, 130, 143, 255)
PALE_SILVER = (184, 190, 201, 255)
IVORY = (246, 249, 252, 255)
GOLD_SHADOW = (127, 85, 22, 255)
GOLD = (207, 154, 38, 255)
GOLD_HIGHLIGHT = (250, 221, 104, 255)
CELESTIAL_RUNE = (255, 212, 53, 255)
CYAN = (57, 210, 229, 255)
PALE_CYAN = (185, 252, 255, 255)

HOLY_FEATHER_PALETTE = (
    CHARCOAL,
    DARK_METAL,
    MID_METAL,
    SILVER,
    PALE_SILVER,
    IVORY,
    GOLD_SHADOW,
    GOLD,
    GOLD_HIGHLIGHT,
    CYAN,
    PALE_CYAN,
)


def recolor_tool(source_name: str, destination_name: str, rune: tuple[int, int, int, int], rune_pixels: tuple[tuple[int, int], ...]) -> None:
    source = Image.open(TEXTURES / source_name).convert("RGBA")
    palette = {
        (17, 17, 17, 255): CHARCOAL,
        (39, 28, 29, 255): DARK_METAL,
        (47, 33, 34, 255): DARK_METAL,
        (49, 41, 42, 255): MID_METAL,
        (50, 39, 39, 255): MID_METAL,
        (59, 57, 59, 255): SILVER,
        (60, 50, 50, 255): SILVER,
        (77, 73, 77, 255): PALE_SILVER,
        (90, 87, 90, 255): PALE_SILVER,
        (117, 40, 2, 255): GOLD_SHADOW,
        (154, 85, 10, 255): GOLD,
        (178, 100, 17, 255): GOLD,
        (233, 177, 21, 255): GOLD_HIGHLIGHT,
        (250, 214, 74, 255): GOLD_HIGHLIGHT,
        (253, 245, 95, 255): IVORY,
        (255, 255, 255, 255): IVORY,
    }
    result = Image.new("RGBA", source.size, TRANSPARENT)
    result.putdata([palette.get(pixel, pixel) for pixel in source.getdata()])
    for x, y in rune_pixels:
        if 0 <= x < 16 and 0 <= y < 16:
            result.putpixel((x, y), rune)
    result.save(TEXTURES / destination_name)


def make_fragment_textures() -> None:
    source = Image.open(WING_REFERENCE).convert("RGBA")
    bounds = source.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError(f"{WING_REFERENCE} contains no visible pixels")

    source = source.crop(bounds)
    source.thumbnail((14, 14), Image.Resampling.NEAREST)
    result = Image.new("RGBA", (16, 16), TRANSPARENT)
    result.alpha_composite(
        source,
        ((16 - source.width) // 2, (16 - source.height) // 2),
    )

    quantized = []
    for red, green, blue, alpha in result.getdata():
        if alpha < 96:
            quantized.append(TRANSPARENT)
            continue
        quantized.append(
            min(
                HOLY_FEATHER_PALETTE,
                key=lambda color: (
                    (red - color[0]) ** 2
                    + (green - color[1]) ** 2
                    + (blue - color[2]) ** 2
                ),
            )
        )
    result.putdata(quantized)
    result.save(TEXTURES / "fragment_of_tyraels_wings.png")


def main() -> None:
    TEXTURES.mkdir(parents=True, exist_ok=True)
    make_fragment_textures()
    variants = (
        ("netherite_pickaxe.png", "divine_pickaxe.png", CELESTIAL_RUNE, ((8, 3), (8, 4), (9, 4), (8, 5))),
        ("netherite_axe.png", "divine_axe.png", CELESTIAL_RUNE, ((7, 3), (7, 4), (8, 4), (7, 5))),
        ("adamant_dolabra.png", "divine_dolabra.png", CELESTIAL_RUNE, ((7, 3), (7, 4), (8, 4), (7, 5))),
    )
    for source, destination, rune, pixels in variants:
        recolor_tool(source, destination, rune, pixels)


if __name__ == "__main__":
    main()
