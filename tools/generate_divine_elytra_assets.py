#!/usr/bin/env python3
"""Generate the original Divine Elytra equipment and inventory textures."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
WING_TEXTURES = ROOT / "assets" / "minecraft" / "textures" / "entity" / "equipment" / "wings"
ITEM_TEXTURES = ROOT / "assets" / "minecraft" / "textures" / "item"

TRANSPARENT = (0, 0, 0, 0)
SHADOW = (92, 101, 111, 255)
FEATHER_SHADE = (179, 188, 195, 255)
FEATHER = (229, 230, 224, 255)
IVORY = (255, 249, 225, 255)
HIGHLIGHT = (255, 255, 250, 255)
GOLD_SHADOW = (133, 89, 26, 255)
GOLD = (222, 172, 65, 255)
GOLD_LIGHT = (255, 231, 148, 255)
CYAN = (82, 227, 239, 255)


def row_bounds(image: Image.Image, y: int) -> tuple[int, int] | None:
    visible = [x for x in range(image.width) if image.getpixel((x, y))[3] > 0]
    if not visible:
        return None
    return min(visible), max(visible)


def make_worn_wings() -> None:
    """Keep vanilla's wing silhouette while painting layered angel feathers."""
    source = Image.open(WING_TEXTURES / "elytra.png").convert("RGBA")
    result = Image.new("RGBA", source.size, TRANSPARENT)

    for y in range(source.height):
        bounds = row_bounds(source, y)
        if bounds is None:
            continue
        left, right = bounds
        width = right - left + 1
        for x in range(left, right + 1):
            alpha = source.getpixel((x, y))[3]
            if not alpha:
                continue
            local_x = x - left
            leading_edge = local_x <= 1
            trailing_edge = local_x >= width - 1
            feather_row = y >= 4 and y % 3 == 1
            feather_tip = y >= 6 and (local_x + y // 2) % 5 == 0
            inner_rib = local_x == max(2, width // 3) and y >= 2

            color = FEATHER
            if feather_row:
                color = FEATHER_SHADE
            elif feather_tip:
                color = IVORY
            if y >= 4 and local_x == max(2, width // 3) + 1:
                color = HIGHLIGHT
            if leading_edge or inner_rib:
                color = GOLD
            if leading_edge and y % 2 == 0:
                color = GOLD_LIGHT
            if trailing_edge:
                color = SHADOW
            if y <= 2:
                color = GOLD_SHADOW if y == 0 else GOLD
            result.putpixel((x, y), (*color[:3], alpha))

    # The small cyan setting reads as a divine clasp at the shoulder.
    for point in ((35, 2), (36, 2), (35, 3)):
        if source.getpixel(point)[3] > 0:
            result.putpixel(point, CYAN)
    result.save(WING_TEXTURES / "tyraels_elytra.png")


def paint_wing(image: Image.Image, mirror: bool) -> None:
    """Paint a wide fan of overlapping feathers for the inventory icon."""
    feather_rows = {
        2: (6, 6),
        3: (5, 6),
        4: (4, 6),
        5: (3, 6),
        6: (2, 6),
        7: (1, 6),
        8: (0, 6),
        9: (0, 5),
        10: (1, 5),
        11: (2, 5),
        12: (3, 5),
        13: (4, 5),
    }
    for y, (start, end) in feather_rows.items():
        for x in range(start, end + 1):
            draw_x = 15 - x if mirror else x
            color = FEATHER
            if x == start:
                color = GOLD_LIGHT if y < 7 else GOLD
            elif y >= 7 and (x + y) % 3 == 0:
                color = FEATHER_SHADE
            elif x == end:
                color = IVORY
            image.putpixel((draw_x, y), color)


def make_inventory_icons() -> None:
    icon = Image.new("RGBA", (16, 16), TRANSPARENT)
    paint_wing(icon, mirror=False)
    paint_wing(icon, mirror=True)
    icon.putpixel((7, 2), GOLD_LIGHT)
    icon.putpixel((8, 2), GOLD_LIGHT)
    icon.putpixel((7, 3), CYAN)
    icon.putpixel((8, 3), CYAN)
    icon.save(ITEM_TEXTURES / "tyraels_elytra.png")

    broken = icon.copy()
    muted = {
        IVORY: FEATHER_SHADE,
        FEATHER_SHADE: SHADOW,
        GOLD: GOLD_SHADOW,
        GOLD_LIGHT: GOLD,
        CYAN: SHADOW,
    }
    broken.putdata([muted.get(pixel, pixel) for pixel in broken.getdata()])
    for point in ((1, 7), (14, 7), (2, 10), (13, 10), (3, 12), (12, 12)):
        broken.putpixel(point, TRANSPARENT)
    broken.save(ITEM_TEXTURES / "tyraels_elytra_broken.png")


def main() -> None:
    make_worn_wings()
    make_inventory_icons()


if __name__ == "__main__":
    main()
